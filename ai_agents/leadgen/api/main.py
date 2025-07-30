from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST"],
    allow_headers=["*"]
)

class SearchRequest(BaseModel):
    query: str
    mode:str

@app.post("/api/v1/search")
async def search(request: SearchRequest):
    try:
        cmd = f'leadgen dsl --{request.mode} "{request.query}"'
        result = subprocess.run(cmd, shell=True, text=True)
        return {"status": "success", "message": "Search completed"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}