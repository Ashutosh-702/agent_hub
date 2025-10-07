"""
Static file serving configuration for production
"""
import os
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from config.loaded_config import loaded_config
from config.logging import logger


def configure_static_serving_production(app: FastAPI):
    """
    Production-ready static file serving with proper error handling
    Uses separate mounting for static assets and catch-all for SPA routing
    """

    static_path = loaded_config.static_path

    if not loaded_config.serve_static:
        logger.info("Static file serving disabled (SERVE_STATIC=false)")
        return

    if not os.path.exists(static_path):
        logger.info(f"Static path does not exist: {static_path}")
        return

    index_path = Path(static_path) / "index.html"

    if not index_path.exists():
        logger.info(f"index.html not found in {static_path}")
        return

    logger.info(f"✓ Serving static files from: {static_path}")

    # Mount static assets
    static_assets_path = Path(static_path) / "app/static"

    if static_assets_path.exists():
        app.mount(
            "/static", StaticFiles(directory=static_assets_path), name="static")
        logger.info(f"✓ Mounted static assets from: {static_assets_path}")

    # Catch-all route for SPA
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # Skip API routes and health checks
        if (full_path.startswith("api/") or
                full_path in ["_healthz", "_readyz", "env-config"]):
            raise HTTPException(status_code=404, detail="Not found")

        file_path = Path(static_path) / full_path

        # Serve static files if they exist
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)

        # Fallback to index.html for SPA routing
        return FileResponse(index_path, headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        })

    logger.info("✓ Static file serving configured successfully")


def get_env_config():
    """Return environment configuration as JavaScript"""
    config = {
        "AGENTHUB_MAIN_DOMAIN": os.getenv("AGENTHUB_MAIN_DOMAIN", "http://0.0.0.0:80"),
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "development"),
        "VERSION": "2.0.0",
        "FEATURES": {
            "document_management": True,
            "advanced_analytics": True,
            "export_functionality": True
        }
    }
    config_json = json.dumps(config)

    js_config = f"""
window.ENV_CONFIG = {config_json};
window.AGENTHUB_MAIN_DOMAIN = "{config['AGENTHUB_MAIN_DOMAIN']}";
window.ENVIRONMENT = "{config['ENVIRONMENT']}";
console.log('Environment configuration loaded:', window.ENV_CONFIG);
"""

    return Response(content=js_config, media_type="application/javascript")
    