import os

from app.api.v1.router import api_router
from app.core.multi_tenant import extract_organization_id
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """
    Health check endpoint for container orchestration.
    """
    return {"status": "ok"}


# Organization context middleware for multi-tenant support
@app.middleware("http")
async def organization_context_middleware(request: Request, call_next):
    """
    Middleware to extract and store organization context for each request.

    This middleware extracts the organization ID from either the JWT token
    or the X-Organization-ID header and stores it in request.state for use
    by downstream handlers. The organization context is used for:
    - Data isolation in multi-tenant architecture
    - Row Level Security (RLS) policy enforcement
    - Authorization checks

    The organization context is optional - endpoints that require it should
    explicitly validate its presence using require_organization_context().

    Args:
        request: Incoming HTTP request
        call_next: Next middleware/handler in the chain

    Returns:
        Response from the next handler

    Note:
        - Organization ID is stored in request.state.organization_id
        - Does not fail if organization ID is not present
        - Individual endpoints are responsible for enforcing organization context
    """
    # Extract organization ID from request (token or header)
    organization_id = extract_organization_id(request)

    # Store in request state for access by endpoints
    if organization_id is not None:
        request.state.organization_id = organization_id

    # Continue processing request
    response = await call_next(request)
    return response


# Include API router
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if os.environ.get("DEBUG") else False,
    )
