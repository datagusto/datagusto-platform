from fastapi import APIRouter

from app.api.v1.endpoints import auth, organizations, projects, traces

api_router = APIRouter()

# Include routers for each endpoint group
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(traces.router, prefix="/traces", tags=["traces"]) 