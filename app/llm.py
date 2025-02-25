import asyncio
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

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


async def stream_llm_response(query: str, sessionid: str):
    async for chunk in tutor_llm.astream({"query": query}):
        yield chunk.content



async def test_stream(query: str):
    async for chunk in stream_llm_response(query):
        print(chunk, flush=True, end="")


if __name__ == "__main__":
    asyncio.run(test_stream("how do pulleys work?"))
