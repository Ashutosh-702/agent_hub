from fastapi.responses import ORJSONResponse, Response
from fastapi.routing import APIRouter
from app.routing import CustomRequestRoute
from ai_agents.leadgen.api.routes import router as leadgen_router
from ai_agents.inbox.routes import router as inbox_router
from ai_agents.meetings.routes import router as meetings_router, ws_router as meetings_ws_router
from ai_agents.auth.routes import router as auth_router
from webhooks.lemlist_inbox_webhook import router as lemlist_webhook_router
from app.static_serving import get_env_config

api_router = APIRouter(route_class=CustomRequestRoute)

router = APIRouter(prefix="/api/v1", route_class=CustomRequestRoute)

router.include_router(leadgen_router)
router.include_router(inbox_router)
router.include_router(meetings_router)

# Auth router is at root level (already has /api/v1/auth prefix)
api_router_auth = APIRouter(route_class=CustomRequestRoute)
api_router_auth.include_router(auth_router)


async def healthz():
    return ORJSONResponse(status_code=200, content={"success": True})


async def readyz():
    return ORJSONResponse(status_code=200, content={"success": True})

api_router_static = APIRouter()
api_router_static.add_api_route(
    "/env-config", methods=["GET"], endpoint=get_env_config, include_in_schema=False)

api_router_healthz = APIRouter()
api_router_healthz.add_api_route(
    "/_healthz", methods=["GET"], endpoint=healthz, include_in_schema=False)
api_router_healthz.add_api_route(
    "/_readyz", methods=["GET"], endpoint=readyz, include_in_schema=False)

api_router.include_router(api_router_healthz, tags=["Healthz"])
api_router.include_router(api_router_static, tags=["config"])
api_router.include_router(api_router_auth)  # Auth routes (login, register, etc.)
api_router.include_router(router)
api_router.include_router(lemlist_webhook_router)
api_router.include_router(meetings_ws_router)  # WebSocket routes at root level
