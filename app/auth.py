from datetime import datetime, timedelta
import sys
import os
import asyncio
import sqlalchemy
import jwt
from sqlalchemy.ext.asyncio import AsyncEngine
from argon2 import PasswordHasher
from pydantic import BaseModel
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from google.cloud.sql.connector import Connector
from dotenv import load_dotenv

from app.db_connection import init_connection_pool

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = "HS512"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

ph = PasswordHasher()

class Token(BaseModel):
    access_token: str
    token_type: str


def create_access_token(data: dict):
    to_encode: dict = data.copy()
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def authenticate_org(
    pool: AsyncEngine,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> bool | str:
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
                return org[0]
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


async def check_for_org(
    pool: AsyncEngine,
    organization: str,
) -> bool:
    try:
        async with pool.connect() as conn:
            result = await conn.execute(sqlalchemy.text(f"""
                SELECT organization FROM "public".Auth WHERE organization = '{organization}'
                """))
            if result.scalar_one():
                return True
            return False
    except Exception as e:
        print(f"Exception occured while trying to check if org exists: {e}", file=sys.stderr)
        return False



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
