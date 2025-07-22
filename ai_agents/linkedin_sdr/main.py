import os
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .routes import upload, batch_processor

# EventBridge imports 
from eventbridge.consumer import setup_and_start_consumer
from eventbridge.health import _healthz, _readyz
from .kafka_config import KAFKA_CONSUMER_SETTINGS
from .constants import LinkedInSDRServices

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
    
    frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
    
    return app

async def main():
    mode = os.getenv("MODE", "server").lower()
    consumer_type = os.getenv("CONSUMER_TYPE", "linkedin_batch_consumer")
    
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
        print("   🌉 Using EventBridge abstraction")
        
        try:
            consumer_config = KAFKA_CONSUMER_SETTINGS[LinkedInSDRServices.linkedin_sdr][consumer_type]
            
            print(f"   ⚙️  Service: {consumer_config['service_name']}")
            print(f"   📂 Topics: {list(consumer_config['topics_configurations'].keys())}")
            
            # Health check endpoints
            print("   ❤️ Starting health check endpoints...")
            asyncio.create_task(_healthz())
            asyncio.create_task(_readyz())
            
            # EventBridge call
            await setup_and_start_consumer(consumer_config)
            
        except KeyError as e:
            available_consumers = list(KAFKA_CONSUMER_SETTINGS.get(LinkedInSDRServices.linkedin_sdr, {}).keys())
            print(f"❌ Unknown consumer type: {consumer_type}")
            print(f"   Available consumer types: {available_consumers}")
            print("   Set CONSUMER_TYPE environment variable")
            print("   Examples:")
            for consumer in available_consumers:
                if not consumer.startswith('#'):
                    print(f"     CONSUMER_TYPE={consumer}")
            
    else:
        print(f"❌ Unknown mode: {mode}")
        print("   Valid modes: 'server' or 'consumer'")
        print("   Set MODE environment variable")
        print("   Examples:")
        print("     MODE=server python main.py")
        print("     MODE=consumer CONSUMER_TYPE=linkedin_batch_consumer python main.py")

if __name__ == "__main__":
    asyncio.run(main())
