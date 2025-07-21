import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .routes import upload, batch_processor
from .kafka_consumer import start_batch_consumer  # Original raw Kafka consumer
from .eventbridge_consumer import start_eventbridge_consumer  # New EventBridge consumer

def create_fastapi_app():
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
    
    @app.get("/health")
    async def health():
        return {"status": "healthy", "mode": "server"}
    
    # This MUST be last since it catches all remaining routes...important to note
    frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
    
    return app

async def main():
    mode = os.getenv("MODE", "server").lower()
    consumer_type = os.getenv("CONSUMER_TYPE", "eventbridge_batch_consumer")
    
    print(f"🚀 Starting LinkedIn SDR in {mode.upper()} mode...")
    
    if mode == "server":
        print("🌐 Starting FastAPI server...")
        print("   📡 API will be available at: http://localhost:8000")
        print("   📋 Health check: http://localhost:8000/health")
        print("   📊 Upload endpoint: http://localhost:8000/api/v1/upload-leads")
        print("   🔄 Process endpoint: http://localhost:8000/api/v1/process-batch/{batch_id}")
        
        import uvicorn
        app = create_fastapi_app()
        port = int(os.getenv("PORT", 8000))
        uvicorn.run(app, host="0.0.0.0", port=port)
        
    elif mode == "consumer":
        print("🤖 Starting Kafka consumer...")
        print(f"   📡 Consumer type: {consumer_type}")
        print("   📨 Listening for Chronos batch processing messages...")
        print("   🔄 Will process LinkedIn URLs one at a time")
        
        if consumer_type == "eventbridge_batch_consumer":
            print("   🌉 Using EventBridge abstraction (RECOMMENDED)")
            await start_eventbridge_consumer(consumer_type="linkedin_batch_consumer")
            
        elif consumer_type == "raw_batch_consumer":
            print("   ⚡ Using raw Kafka consumer (LEGACY)")
            await start_batch_consumer()
            
        else:
            print(f"❌ Unknown consumer type: {consumer_type}")
            print("   Valid consumer types:")
            print("     - 'eventbridge_batch_consumer' (EventBridge - RECOMMENDED)")
            print("     - 'raw_batch_consumer' (Raw Kafka - LEGACY)")
            
    else:
        print(f"❌ Unknown mode: {mode}")
        print("   Valid modes: 'server' or 'consumer'")
        print("   Set MODE environment variable")
        print("   Examples:")
        print("     MODE=server python main.py")
        print("     MODE=consumer CONSUMER_TYPE=eventbridge_batch_consumer python main.py")
        print("     MODE=consumer CONSUMER_TYPE=raw_batch_consumer python main.py")

if __name__ == "__main__":
    asyncio.run(main())
