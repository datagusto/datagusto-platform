"""
Dependency injection functions for FastAPI endpoints.
Provides standardized service layer dependencies with repository injection.
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.project_repository import ProjectRepository
from app.repositories.project_member_repository import ProjectMemberRepository  
from app.repositories.organization_member_repository import OrganizationMemberRepository
from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.trace_repository import TraceRepository
from app.services.project_service import ProjectService
from app.services.organization_service import OrganizationService
from app.services.trace_service import TraceService
from app.services.auth_service import AuthService


async def get_project_service(db: Session = Depends(get_db)) -> ProjectService:
    """
    Create ProjectService with all required repository dependencies.
    
    Args:
        db: Database session dependency
        
    Returns:
        Configured ProjectService instance
    """
    project_repo = ProjectRepository(db)
    project_member_repo = ProjectMemberRepository(db)
    org_member_repo = OrganizationMemberRepository(db)
    
    return ProjectService(
        project_repo=project_repo,
        project_member_repo=project_member_repo,
        org_member_repo=org_member_repo
    )


async def get_organization_service(db: Session = Depends(get_db)) -> OrganizationService:
    """
    Create OrganizationService with all required repository dependencies.
    
    Args:
        db: Database session dependency
        
    Returns:
        Configured OrganizationService instance
    """
    org_repo = OrganizationRepository(db)
    org_member_repo = OrganizationMemberRepository(db)
    
    return OrganizationService(
        org_repo=org_repo,
        org_member_repo=org_member_repo
    )


async def get_trace_service(db: Session = Depends(get_db)) -> TraceService:
    """
    Create TraceService with all required repository dependencies.
    
    Args:
        db: Database session dependency
        
    Returns:
        Configured TraceService instance
    """
    # TraceService is a static class, but we return it for consistency
    return TraceService