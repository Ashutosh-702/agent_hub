from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import subprocess

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class SearchRequest(BaseModel):
    query: str
    mode: str

@app.post("/api/v1/search")
async def search(request: SearchRequest):
    try:
        cmd = f'leadgen dsl --{request.mode} "{request.query}"'
        result = subprocess.run(cmd, shell=True, text=True)
        return {"status": "success", "message": "Search completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/v1/search/stream")
async def stream_logs(query: str, mode: str):
    async def event_generator():
        command = f'leadgen dsl --{mode} "{query}"'

        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in iter(process.stdout.readline, ""):
            yield f"data: {line.strip()}\n\n"

        process.stdout.close()
        process.wait()

    return EventSourceResponse(event_generator())