from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse
import asyncio

load_dotenv()

app = FastAPI()

origins = ["http://localhost", "http://localhost:3000", "https://malthusia.art"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def followfile(fname: str):
    proc = await asyncio.create_subprocess_exec(
        "tail", "-F", fname, stdout=asyncio.subprocess.PIPE
    )
    while True:
        bs = await proc.stdout.read(n=1000)
        yield bs


@app.get("/replay")
async def replay():
    return StreamingResponse(followfile("../engine/replay.gz"), media_type="application/replay")