from fastapi.responses import ORJSONResponse, Response
from fastapi.routing import APIRouter
from app.routing import CustomRequestRoute
from ai_agents.leadgen.api.routes import router as leadgen_router
from app.static_serving import get_env_config

api_router = APIRouter(route_class=CustomRequestRoute)

router = APIRouter(prefix="/api/v1", route_class=CustomRequestRoute)

router.include_router(leadgen_router)


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
api_router.include_router(router)
