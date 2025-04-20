from fastapi import APIRouter

from app.api.v1.api import api_router as api_router_v1

api_router = APIRouter()

# Include versioned routers
api_router.include_router(api_router_v1, prefix="/v1")
