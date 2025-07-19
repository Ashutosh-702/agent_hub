from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import upload, batch_processor

app = FastAPI(
    title="LinkedIn SDR",
    description="LinkedIn connection automation System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
app.include_router(batch_processor.router, prefix="/api/v1", tags=["batch"])

@app.get("/")
async def root():
    return {"message": "LinkedIn SDR is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
