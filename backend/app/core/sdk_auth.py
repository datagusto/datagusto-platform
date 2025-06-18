from fastapi import HTTPException, Header, Depends
from sqlalchemy.orm import Session
from typing import Annotated

from app.core.database import get_db
from app.models import Project


async def get_project_from_api_key(
    x_api_key: Annotated[str, Header()],
    db: Session = Depends(get_db)
) -> Project:
    """Authenticate SDK requests using API key and return the associated project."""
    
    project = db.query(Project).filter(Project.api_key == x_api_key).first()
    
    if not project:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return project