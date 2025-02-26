import sys
import asyncio
from fastapi.datastructures import Default
from google.cloud.sql.connector import Connector
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import sqlalchemy
from sqlalchemy.ext.asyncio.engine import AsyncEngine
from starlette.responses import StreamingResponse
from dotenv import load_dotenv

from app.llm import get_graph, stream_llm_response, Graph
from app.db_connection import init_connection_pool

load_dotenv()

pool: None | AsyncEngine = None


async def lifespan(app: FastAPI):
    global Graph
    Graph = await get_graph()
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
    userid: int
    sessionid: int
    message: str


@app.post("/stream_query")
async def wrapper(query: Query) -> StreamingResponse:
    userid = query.userid
    sessionid = query.sessionid
    message = query.message


    async with pool.connect() as conn:
        await conn.execute(sqlalchemy.text(
            f"INSERT INTO users(userid) VALUES({userid}) ON CONFLICT (userid) DO NOTHING;"
        ))

        await conn.execute(sqlalchemy.text(
            f"INSERT INTO Sessions(sessionid, userid, created_at) VALUES(DEFAULT, {userid}, DEFAULT) ON CONFLICT (sessionid) DO NOTHING;"
        ))
        await conn.commit()




    response = StreamingResponse(
        stream_llm_response(message, sessionid, userid), media_type="text/event-stream")
    return response
