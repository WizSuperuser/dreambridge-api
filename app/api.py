import sys
import asyncio
from dataclasses import InitVar
from warnings import _W
from google.cloud.sql.connector import Connector
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlalchemy
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from starlette.responses import StreamingResponse
from dotenv import load_dotenv

from app.llm import stream_llm_response
from app.db_connection import init_connection_pool

load_dotenv()

pool: None | AsyncEngine = None

async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    async with Connector(loop=loop) as connector:
        global pool
        try:
            pool = await init_connection_pool(connector)
            yield
            await pool.dispose()
        except Exception as e:
            print(f"Exception when trying to connect to database: {e}", file=sys.stderr)
        # finally?

app: FastAPI = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    async with pool.connect() as conn:
        val = await conn.execute(
            sqlalchemy.text("""
                SELECT NOW();
                """)
        )
    return {"Hello": f"{val.fetchall()}"}


class Query(BaseModel):
    userid: str
    chatid: str | None
    message: str


@app.post("/stream_query")
async def wrapper(query: Query) -> StreamingResponse:
    userid = query.userid
    chatid = query.chatid
    message = query.message

    async with pool.connect() as conn:
        val = await conn.execute(sqlalchemy.text(f"select exists(select 1 from sessions where sessionid::text='{chatid}')"))
        if val.fetchall()[0][0] == False:
            data = ({"user_id": userid})
            await conn.execute(sqlalchemy.text(
                f"INSERT INTO session(sessionid, user_id, created_at) VALUES(DEFAULT, {userid}, DEFAULT);"
            ))
            await conn.commit()


    response = StreamingResponse(
        stream_llm_response(message, chatid), media_type="text/event-stream"
    )
    return response
