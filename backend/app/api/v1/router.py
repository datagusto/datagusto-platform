from fastapi import APIRouter

from app.api.v1.endpoints import (
    agents,
    auth,
    guardrails,
    organizations,
    projects,
    public_guardrails,
    safety,
    traces,
    users,
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(
    organizations.router, prefix="/organizations", tags=["organizations"]
)
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(guardrails.router, prefix="/guardrails", tags=["guardrails"])
api_router.include_router(traces.router, prefix="/traces", tags=["traces"])
api_router.include_router(
    public_guardrails.router, prefix="/public/guardrails", tags=["public-guardrails"]
)
api_router.include_router(safety.router, prefix="/public/safety", tags=["safety"])
