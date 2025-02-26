import json
import asyncio
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_openai.embeddings.base import _process_batched_chunked_embeddings
from langgraph.graph import MessagesState, StateGraph, START, END
from dotenv import load_dotenv
from langgraph.pregel.loop import Checkpoint

from app.db_connection import get_checkpointer

load_dotenv()

class State(MessagesState):
    summary: str


def responder(State):
    pass


def if_summarize(State):
    pass


def summarizer(State):
    pass


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

    checkpointer = await get_checkpointer()

    graph = workflow.compile(checkpointer=checkpointer)
    return graph

Graph = None

llm = ChatOpenAI(
    model="gpt-4o-mini",
)

template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Help the student resolve their query by providing thorough, detailed answers. Use math equations and problems where they are illustrative. Make sure the answer is complete and gives both an intuitive and rigorous understanding to the student. Ask a question at the end to test the student's understanding and provide a thoughtful next question for the student to think about.",
        ),
        ("user", "{query}"),
    ]
)

tutor_llm = template | llm


async def stream_llm_response(query: str, sessionid: int, userid: int):
    async for chunk in tutor_llm.astream({"query": query}):
        yield chunk.content



async def test_stream(query: str):
    async for chunk in stream_llm_response(query, 1, 1):
        print(chunk, flush=True, end="")


if __name__ == "__main__":
    asyncio.run(test_stream("how do pulleys work?"))
