"""Main entry point for the agent hub application."""

import uvicorn
from config.loaded_config import loaded_config


def main() -> None:
    """Entrypoint of the application."""
    # When reload is enabled (debug mode), workers must be 1
    workers = 1 if loaded_config.debug else loaded_config.workers
    
    print(f"🚀 Starting server on {loaded_config.host}:{loaded_config.port}")
    print(f"🔄 Hot reload: {'enabled' if loaded_config.debug else 'disabled'}")
    print(f"👥 Workers: {workers}")
    
    uvicorn.run(
        "app.application:get_app",
        host=loaded_config.host,
        port=loaded_config.port,
        reload=loaded_config.debug,
        workers=workers,
        factory=True,
    )
