import os
from dotenv.main import load_dotenv
import httpx

load_dotenv()

username = os.environ.get("ROOT_ORG")
password = os.environ.get("ROOT_PASSWORD")
production_url = os.environ.get("PRODUCTION_URL")
url = "http://localhost:8000"

with httpx.Client(base_url=production_url) as client:
    response = client.post(
        "/token",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    response.raise_for_status()

print(response.json()["access_token"])

token = response.json()["access_token"]


with httpx.stream(
    "POST",
    f"{production_url}/stream-query",
    json={
        "user_id": 12,
        "session_id": 1,
        "message": "Do pulleys let you exert less force than you would need without them? If so, how?",
    },
    headers={"Authorization": f"Bearer {token}"},
) as r:
    r.raise_for_status()
    print(r.status_code)
    print(type(r))
    for chunk in r.iter_raw():
        print(chunk.decode(encoding="utf-8"), end="", flush=True)
