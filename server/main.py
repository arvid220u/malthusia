from ratelimiter import RateLimiter
from fakedb import FakeDB
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse
import json

RATE_LIMIT = 100

load_dotenv()

db = FakeDB()

app = FastAPI()

rl = RateLimiter(db, RATE_LIMIT)

origins = ["http://localhost", "http://localhost:3000", "https://malthusia.art"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def followfile(fname: string):
    yield "hi"


@app.get("/replay")
async def replay():
    with open("../engine/replay.json", "r") as f:
        d = json.load(f)
    return StreamingResponse(followfile("../engine/replay.gz"), media_type="application/replay")