"""
Static file serving configuration for production
"""
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from config.loaded_config import loaded_config


def configure_static_serving_production(app: FastAPI):
    """
    Production-ready static file serving with proper error handling
    Uses separate mounting for static assets and catch-all for SPA routing
    """

    static_path = loaded_config.static_path

    if not loaded_config.serve_static:
        print("Static file serving disabled (SERVE_STATIC=false)")
        return

    if not os.path.exists(static_path):
        print(f"WARNING: Static path does not exist: {static_path}")
        return

    index_path = Path(static_path) / "index.html"

    if not index_path.exists():
        print(f"WARNING: index.html not found in {static_path}")
        return

    print(f"✓ Serving static files from: {static_path}")

    # Mount static assets
    static_assets_path = Path(static_path) / "app/static"

    if static_assets_path.exists():
        app.mount(
            "/static", StaticFiles(directory=static_assets_path), name="static")
        print(f"✓ Mounted static assets from: {static_assets_path}")

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

    print("✓ Static file serving configured successfully")
    