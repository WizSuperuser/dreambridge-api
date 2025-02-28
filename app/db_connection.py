import asyncio
import os
from functools import lru_cache

import asyncpg
import sqlalchemy
from dotenv import load_dotenv
from google.cloud.sql.connector import Connector, IPTypes
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool, ConnectionPool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

load_dotenv()

instance_connection_name = os.environ["INSTANCE_CONNECTION_NAME"]
db_user = os.environ["DB_USER"]
db_pass = os.environ["DB_PASS"]
db_name = os.environ["DB_NAME"]
db_ip_addr = os.environ["DB_IP_ADDR"]


# docs: https://github.com/GoogleCloudPlatform/cloud-sql-python-connector#usage
@lru_cache
async def init_connection_pool(connector: Connector) -> AsyncEngine:

    async def get_conn() -> asyncpg.Connection:
        conn: asyncpg.Connection = await connector.connect_async(
            instance_connection_name,
            "asyncpg",
            user=db_user,
            password=db_pass,
            db=db_name,
            ip_type=IPTypes.PRIVATE
            if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC,
        )
        return conn

    pool = create_async_engine(
        "postgresql+asyncpg://",
        async_creator=get_conn,
    )

    return pool


async def create_tables():
    loop = asyncio.get_running_loop()
    async with Connector(loop=loop) as connector:
        pool = await init_connection_pool(connector)

        async with pool.connect() as conn:
            await conn.execute(
                sqlalchemy.text("""
                    CREATE TABLE IF NOT EXISTS "public".Users (
                    user_id integer PRIMARY KEY
                );
                    """))

            # await conn.execute(
            #     sqlalchemy.text("""
            #         CREATE TABLE IF NOT EXISTS "public".Tasks (
            #         taskid integer PRIMARY KEY,
            #         task VARCHAR(255) CHECK (task IN ('task1', 'task2', 'task3', 'task4', 'task5'))
            #     );
            #         """)
            #     # add distict for tasks here so that only one id per task
            # )

            await conn.execute(
                sqlalchemy.text("""
                    CREATE TABLE IF NOT EXISTS "public".Sessions (
                        session_id integer PRIMARY KEY,
                        user_id integer NOT NULL REFERENCES Users(user_id),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """))

            # await conn.execute(
            #     sqlalchemy.text("""
            #         CREATE TABLE IF NOT EXISTS "public".Messages (
            #             messageid integer PRIMARY KEY,
            #             session_id integer REFERENCES Sessions(session_id),
            #             taskid integer REFERENCES Tasks(taskid),
            #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            #         );
            #         """)
            # )

            await conn.commit()

        await pool.dispose()


def setup_checkpointer():
    connection_str = (
        f"host={db_ip_addr} port=5432 dbname={db_name} user={db_user} password={db_pass}"
    )

    with ConnectionPool(conninfo=connection_str, ) as pool:
        with pool.connection() as conn:
            conn.autocommit = True

            checkpointer = PostgresSaver(conn)
            checkpointer.setup()


async def get_checkpointer():
    connection_str = (
        f"host={db_ip_addr} port=5432 dbname={db_name} user={db_user} password={db_pass}"
    )

    pool = AsyncConnectionPool(conninfo=connection_str, open=False)
    await pool.open()
    checkpointer = AsyncPostgresSaver(pool)

    return checkpointer, pool

    # await connector.close_async()

async def test_checkpointer():

    checkpointer, pool = await get_checkpointer()
    val = await checkpointer.aget(config={"configurable": {"thread_id": 1}})
    print(val)

if __name__ == "__main__":
    # pass
    # asyncio.run(create_tables())
    setup_checkpointer()
    # asyncio.run(test_checkpointer())
