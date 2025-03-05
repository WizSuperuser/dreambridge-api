import sys
import asyncio
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlalchemy
from dotenv import load_dotenv
from prometheus_fastapi_instrumentator import Instrumentator

from app.llm import router as llm_router

load_dotenv()

app: FastAPI = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

istrumentator = Instrumentator().instrument(app).expose(app)

@app.get("/")
async def root():
    return {"Hello": "World"}


app.include_router(llm_router)
