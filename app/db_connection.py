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
            ip_type=IPTypes.PRIVATE if os.environ.get("PRIVATE_IP") else IPTypes.PUBLIC,
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
                    CREATE TABLE IF NOT EXISTS "public".users (
                    userid UUID PRIMARY KEY DEFAULT gen_random_uuid()
                );
                    """)
            )

            await conn.execute(
                sqlalchemy.text("""
                    CREATE TABLE IF NOT EXISTS "public".tasks (
                    taskid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    task VARCHAR(255) CHECK (task IN ('task1', 'task2', 'task3', 'task4', 'task5'))
                );
                    """)
                # add distict for tasks here so that only one id per task
            )

            await conn.execute(
                sqlalchemy.text("""
                    CREATE TABLE IF NOT EXISTS "public".Sessions (
                        sessionid UUID PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
                        user_id UUID REFERENCES Users(userid),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """)
            )

            await conn.execute(
                sqlalchemy.text("""
                    CREATE TABLE IF NOT EXISTS "public".messages (
                        messageid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        sessionid UUID REFERENCES sessions(sessionid),
                        taskid UUID REFERENCES tasks(taskid),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    """)
            )

            await conn.commit()

        await pool.dispose()


def setup_checkpointer():
    connection_str = (
        f"host=localhost port=5432 dbname={db_name} user={db_user} password={db_pass}"
    )

    with ConnectionPool(
        conninfo=connection_str,
    ) as pool:
        with pool.connection() as conn:
            conn.autocommit = True

            checkpointer = PostgresSaver(conn)
            checkpointer.setup()


async def get_checkpointer():
    connection_str = (
        f"host=localhost port=5432 dbname={db_name} user={db_user} password={db_pass}"
    )

    async with AsyncConnectionPool(conninfo=connection_str) as pool:
        async with pool.connection() as conn:
            conn.autocommit = True
            checkpointer = AsyncPostgresSaver(conn)

    return checkpointer

    # await connector.close_async()


if __name__ == "__main__":
    pass
    # setup_checkpointer()
