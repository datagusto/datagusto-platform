import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

# Application configuration is loaded from settings
app = FastAPI(
    title="datagusto",
    description="Backend API for datagusto service",
    version="1.0.0",
    docs_url="/docs" if os.environ.get("DEBUG") else None,
    redoc_url="/redoc" if os.environ.get("DEBUG") else None,
)

# Set up CORS using configuration settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True if os.environ.get("DEBUG") else False) 