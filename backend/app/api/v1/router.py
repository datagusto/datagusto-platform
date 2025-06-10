from fastapi import APIRouter

from app.api.v1.endpoints import auth

api_router = APIRouter()

# Include routers for each endpoint group
api_router.include_router(auth.router, prefix="/auth", tags=["auth"]) 