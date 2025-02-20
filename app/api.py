from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse
from dotenv import load_dotenv

load_dotenv()

from app.llm import stream_llm_response

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"Hello": "World"}


class Query(BaseModel):
    userid: str
    chatid: str
    message: str


@app.post("/stream_query")
async def wrapper(query: Query):
    userid = query.userid
    chatid = query.chatid
    message = query.message
    response = StreamingResponse(
        stream_llm_response(message), media_type="text/event-stream"
    )
    return response
