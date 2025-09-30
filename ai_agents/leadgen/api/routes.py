from fastapi import APIRouter, Depends

from app.routing import CustomRequestRoute
from config.loaded_config import loaded_config

router = APIRouter(tags=["AI Agents"], route_class=CustomRequestRoute)
