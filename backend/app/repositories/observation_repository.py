from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from uuid import UUID

from app.models.trace import Observation


class ObservationRepository:
    """Repository for database observation operations."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository with a database session.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def create_observation(self, observation_data: Dict[str, Any]) -> Observation:
        """
        Create a new observation in the database.
        
        Args:
            observation_data: Observation data
            
        Returns:
            Created observation
        """
        observation = Observation(**observation_data)
        self.db.add(observation)
        return observation
    
    async def get_parent_observation(self, trace_id: UUID, external_id: str, platform_type: str) -> Optional[Observation]:
        """
        Get parent observation by external ID.
        
        Args:
            trace_id: Trace ID
            external_id: External observation ID
            platform_type: Platform type
            
        Returns:
            Parent observation or None
        """
        return (
            self.db.query(Observation)
            .filter(
                and_(
                    Observation.trace_id == trace_id,
                    Observation.external_id == external_id,
                    Observation.platform_type == platform_type,
                )
            )
            .first()
        )