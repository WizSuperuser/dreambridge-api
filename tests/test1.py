import httpx

url = "http://localhost:8000/stream_query"

with httpx.stream(
    "GET",
    url,
    json={
        "userid": "ok",
        "chatid": "ok",
        "message": "Do pulleys let you exert less force than you would need without them? If so, how?",
    },
) as r:
    for chunk in r.iter_raw():
        print(chunk.decode(encoding="utf-8"), end="", flush=True)
