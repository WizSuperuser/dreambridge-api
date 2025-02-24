import os
import asyncio
from dotenv import load_dotenv
from google.cloud.sql.connector import Connector, IPTypes
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
import asyncpg

load_dotenv()


# docs: https://github.com/GoogleCloudPlatform/cloud-sql-python-connector#usage
async def init_connection_pool(connector: Connector) -> AsyncEngine:
    async def get_conn() -> asyncpg.Connection:
        instance_connection_name = os.environ["INSTANCE_CONNECTION_NAME"]
        db_user = os.environ["DB_USER"]
        db_pass = os.environ["DB_PASS"]
        db_name = os.environ["DB_NAME"]

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
            val = await conn.execute(sqlalchemy.text("SELECT NOW()"))
            print(val.first())

        await pool.dispose()


if __name__ == "__main__":
    asyncio.run(create_tables())
