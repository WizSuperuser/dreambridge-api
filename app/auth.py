import sys
import os
import asyncio
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncEngine
from argon2 import PasswordHasher
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from google.cloud.sql.connector import Connector
from dotenv import load_dotenv

from app.db_connection import init_connection_pool

ph = PasswordHasher()


async def authenticate_org(
    pool: AsyncEngine,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> bool:
    try:
        async with pool.connect() as conn:
            result = await conn.execute(
                sqlalchemy.text(f"""
                    SELECT organization, hashed_password FROM "public".Auth
                    WHERE organization = '{form_data.username}'
                    """)
            )
            org = result.one()
            if org and len(org) == 2 and ph.verify(org[1], form_data.password):
                return True
            return False
    except Exception as e:
        print(f"Exception while trying to authenticate user: {e}", file=sys.stderr)
        return False


async def add_org(
    pool: AsyncEngine,
    organization: str,
    password: str,
):
    try:
        async with pool.connect() as conn:
                await conn.execute(sqlalchemy.text(f"""
                    INSERT INTO "public".Auth (organization, hashed_password)
                    VALUES('{organization}', '{ph.hash(password)}')
                    """))
                await conn.commit()
    except Exception as e:
        print(f"Exception occured while trying to add org to auth database: {e}", file=sys.stderr)


async def main():
    root_org = os.environ.get("DRBR_ORG", "")
    root_pass = os.environ.get("DRBR_PASSWORD", "")

    try:
        loop = asyncio.get_running_loop()
        async with Connector(loop=loop) as connector:
            pool = await init_connection_pool(connector)
            # Add org to auth database
            # await add_org(pool, root_org, root_pass)

            # Authenticate test
            form_data = OAuth2PasswordRequestForm(
                username=root_org,
                password=root_pass,
            )
            auth = await authenticate_org(pool, form_data)
            print(auth)
    except Exception as e:
        print(f"Exception while trying to connect to pool or authenticate org: {e}", file=sys.stderr)



if __name__ == "__main__":
    asyncio.run(main())
