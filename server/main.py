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


# TODO: start from a specific offset
async def followfile(fname: str):
    proc = await asyncio.create_subprocess_exec(
        "tail", "-c", "+0", "-F", fname, stdout=asyncio.subprocess.PIPE
    )
    N = 100_000
    wait_timeout = 5
    while True:
        try:
            bs = await asyncio.wait_for(proc.stdout.read(n=N), wait_timeout)
        except asyncio.exceptions.TimeoutError:
            bs = b""
        if len(bs) == 0:
            break
        else:
            yield bs

    proc.terminate()


@app.get("/replay")
async def replay():
    # we cannot simply set Content-Encoding: gzip, because our replay file format is several gzips concatenated together
    # while this is okay by the original gzip standard, it is not okay by most browsers...
    return StreamingResponse(followfile("../engine/replay.gz"), media_type="application/replay")#, headers={"Content-Encoding": "gzip"})