from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import ORJSONResponse
from fastapi.middleware.cors import CORSMiddleware
from structlog.contextvars import bind_contextvars

from app.router import api_router
from app.static_serving import configure_static_serving_production
from config.logging import logger
from config.loaded_config import loaded_config
from global_utils.web_app import run_on_startup, run_on_shutdown


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    bind_contextvars(operation="application_startup",
                     component="application_lifecycle", event_type="startup")
    logger.info("🚀 Starting Lead Generation API server...")

    try:
        await run_on_startup()
        logger.info("✅ server Startup successful")

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

    yield  # Server is running

    # Shutdown
    bind_contextvars(operation="application_shutdown",
                     component="application_lifecycle", event_type="shutdown")
    logger.info("🔒 Shutting down Lead Generation API server...")

    try:
        await run_on_shutdown()
        logger.info("✅ server Shutdown successful")

    except Exception as e:
        logger.error(f"❌ Shutdown failed: {e}")


def get_app() -> FastAPI:
    """
    Get FastAPI application.

    This is the main constructor of an application.

    :return: application.
    """

    agent_app = FastAPI(
        debug=loaded_config.debug,
        title="Agent Hub API",
        version="0.1.0",
        description="FastAPI-based agent hub",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
        openapi_url="/swagger.json",
    )

    agent_app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost",
            "http://localhost:80",
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1",
            "http://127.0.0.1:80",
            "http://127.0.0.1:5173",
            "https://ai-sdr.tmsz0.de",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    agent_app.include_router(api_router)
    configure_static_serving_production(agent_app)

    def custom_openapi(app: FastAPI):
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        paths = {}

        for path, path_item in openapi_schema["paths"].items():
            paths[f"{path}"] = path_item

        openapi_schema["paths"] = paths

        return openapi_schema

    agent_app.openapi_schema = custom_openapi(app=agent_app)

    return agent_app
