"""Main entry point for the agent hub application."""

import uvicorn
from config.loaded_config import loaded_config

def main() -> None:
    """Entrypoint of the application."""
    uvicorn.run(
        "app.application:get_app",
        host=loaded_config.host,
        port=loaded_config.port,
        reload=loaded_config.debug,
        workers=loaded_config.workers,
        factory=True,
    )
