from fastapi import APIRouter

from app.api.v1.endpoints import (
    agents,
    auth,
    # organizations,
    traces,
    # evaluators,
    sdk,
    users
)

api_router = APIRouter()

# Include routers for each endpoint group
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(traces.router, prefix="/traces", tags=["traces"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
# api_router.include_router(evaluators.router, prefix="/evaluators", tags=["evaluators"])
api_router.include_router(sdk.router, prefix="/sdk", tags=["sdk"]) 