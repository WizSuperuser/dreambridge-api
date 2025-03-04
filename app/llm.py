import asyncio
import os
import sys
from contextlib import asynccontextmanager
from typing import Annotated

import jwt
from jwt.exceptions import InvalidTokenError
import sqlalchemy
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from google.cloud.sql.connector import Connector
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.message import RemoveMessage
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel
from sqlalchemy.ext.asyncio.engine import AsyncEngine

from app.auth import ALGORITHM, SECRET_KEY, authenticate_org, check_for_org, create_access_token, Token
from app.db_connection import get_checkpointer, init_connection_pool

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini")
llm_backup = ChatGroq(model="llama-3.3-70b-versatile", stop_sequences=None)


class State(MessagesState):
    summary: str
    last_summary: int


def responder(state: State):
    prompt = """Help the student resolve their query by providing thorough, detailed answers.
    Use math equations and problems where they are illustrative.
    Make sure the answer is complete and gives both an intuitive and rigorous understanding to the student.
    Ask a question at the end to test the student's understanding and provide a thoughtful next question for the student to think about."""

    prompt = [SystemMessage(prompt)]

    messages = state["messages"]
    last_summary = state.get("last_summary", 0)
    summary = state.get("summary", "")
    if summary:
        summary_message = f"""
        Summary of the conversation so far: {summary}
        Recent conversation:
        """
        messages_in_prompt = last_summary if last_summary > 0 else 2
        prompt += ([HumanMessage(content=summary_message)] +
                   messages[:messages_in_prompt])

    else:
        prompt += messages

    try:
        response = llm.invoke(prompt)
    except Exception:
        response = llm_backup.invoke(prompt)
    return {"messages": response, "last_summary": last_summary + 2}


def if_summarize(state: State):
    """Return whether to summarize based on length of unsummarized messages."""
    SUMMARIZE_AFTER_MESSAGES = 6

    if state["last_summary"] > SUMMARIZE_AFTER_MESSAGES:
        return "summarize"
    return END


def summarizer(state: State):
    summary = state.get("summary", "")

    if summary:
        summary_message = (
            f"This is the summary of the conversation to date: {summary}\n\n"
            "Be concise and extend the summary by taking into account the new messages above. Make a note of any observations on learner reactions and understanding as well:"
        )
        messages = state["messages"][:state["last_summary"]] + [
            HumanMessage(content=summary_message)
        ]
    else:
        summary_message = "\nCreate a summary of the conversation above. Make a note of any observations on learner reactions and understanding as well:"
        messages = state["messages"] + [summary_message]

    try:
        response = llm.invoke(messages)
    except Exception:
        response = llm_backup.invoke(messages)

    return {"summary": response.content, "last_summary": 0}


async def get_graph():
    workflow = StateGraph(State)
    workflow.add_node("response", responder)
    workflow.add_node("summarize", summarizer)

    workflow.add_edge(START, "response")
    workflow.add_conditional_edges("response", if_summarize, {
        "summarize": "summarize",
        END: END
    })
    workflow.add_edge("summarize", END)

    checkpointer, pool = await get_checkpointer()

    graph = workflow.compile(checkpointer=checkpointer)
    return graph, pool


graph: CompiledStateGraph
checkpointer_pool = None
pool: AsyncEngine


async def lifespan(app: APIRouter):
    global graph
    global checkpointer_pool
    try:
        graph, checkpointer_pool = await get_graph()
    except Exception as e:
        print(f"Exception when trying to connect checkpointer: {e}",
              file=sys.stderr)
    loop = asyncio.get_running_loop()
    async with Connector(loop=loop) as connector:
        global pool
        try:
            pool = await init_connection_pool(connector)
        except Exception as e:
            print(f"Exception when trying to connect to database: {e}",
                  file=sys.stderr)
    yield
    if checkpointer_pool:
        await checkpointer_pool.close()
    if pool:
        await pool.dispose()


router = APIRouter(lifespan=lifespan)


@router.get("/health-check")
async def db_health() -> dict[str, str]:
    async with pool.connect() as conn:
        val = await conn.execute(
            sqlalchemy.text("""
                SELECT NOW();
                """))
    return {"Hello": f"{val.fetchall()}"}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def stream_llm_response(query: str, session_id: int, user_id: int):
    config = {"configurable": {"thread_id": str(session_id)}}
    input = HumanMessage(content=query)
    async for event in graph.astream_events(
        {"messages": input},
            config,
            version="v2",
    ):
        if (event["event"] == "on_chat_model_stream" and event.get(
                "metadata", {}).get("langgraph_node") == "response"):
            data = event["data"]
            if chunk := data.get("chunk"):
                yield chunk.content


class Query(BaseModel):
    user_id: int
    session_id: int
    message: str


@router.post("/token")
async def login_for_token(
    form_data: Annotated[OAuth2PasswordRequestForm,
                         Depends()], ) -> dict:
    if not await authenticate_org(pool, form_data):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_org(
    token: Annotated[str, Depends(oauth2_scheme)],
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    except Exception as e:
        print("Exception while trying to get current org: {e}", file=sys.stderr)
    if check_for_org(pool, username):
        return username



@router.post("/stream-query")
async def wrapper(
    token: Annotated[str, Depends(get_current_org)],
    query: Query,
) -> StreamingResponse:
    user_id = query.user_id
    session_id = query.session_id
    message = query.message

    async with pool.connect() as conn:
        await conn.execute(
            sqlalchemy.text(
                f"INSERT INTO Users(user_id) VALUES({user_id}) ON CONFLICT (user_id) DO NOTHING;"
            ))

        await conn.execute(
            sqlalchemy.text(
                f"INSERT INTO Sessions(session_id, user_id, created_at) VALUES({session_id}, {user_id}, DEFAULT) ON CONFLICT (session_id) DO NOTHING;"
            ))
        await conn.commit()

    response = StreamingResponse(
        stream_llm_response(message, session_id, user_id),
        media_type="text/event-stream",
    )
    return response


async def test_stream(query: str):
    async for chunk in stream_llm_response(query, 1, 1):
        print(chunk, flush=True, end="")


if __name__ == "__main__":
    asyncio.run(test_stream("how do pulleys work?"))
