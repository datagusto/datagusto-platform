from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from uuid import UUID
from datetime import datetime

from app.models.trace import Trace


class TraceRepository:
    """Repository for database trace operations."""
    
    def __init__(self, db: Session):
        """
        Initialize the repository with a database session.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def get_existing_trace(self, project_id: str, external_id: str, platform_type: str) -> Optional[Trace]:
        """
        Get an existing trace by external ID.
        
        Args:
            project_id: Project ID
            external_id: External trace ID
            platform_type: Platform type (e.g., "langfuse")
            
        Returns:
            Existing trace or None
        """
        return (
            self.db.query(Trace)
            .filter(
                and_(
                    Trace.project_id == project_id,
                    Trace.external_id == external_id,
                    Trace.platform_type == platform_type,
                )
            )
            .first()
        )
    
    async def create_trace(self, trace_data: Dict[str, Any]) -> Trace:
        """
        Create a new trace in the database.
        
        Args:
            trace_data: Trace data
            
        Returns:
            Created trace
        """
        trace = Trace(**trace_data)
        self.db.add(trace)
        self.db.flush()  # Get the trace ID for observations
        return trace
    
    async def update_trace(self, trace: Trace, update_data: Dict[str, Any]) -> Trace:
        """
        Update an existing trace.
        
        Args:
            trace: Trace to update
            update_data: Data to update
            
        Returns:
            Updated trace
        """
        for key, value in update_data.items():
            setattr(trace, key, value)
        return trace
    
    async def get_traces_by_project(self, project_id: str, limit: int = 50, offset: int = 0) -> List[Trace]:
        """
        Get traces for a specific project.
        
        Args:
            project_id: Project ID
            limit: Number of traces to return
            offset: Number of traces to skip
            
        Returns:
            List of traces
        """
        return (
            self.db.query(Trace)
            .filter(Trace.project_id == project_id)
            .order_by(desc(Trace.timestamp))
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    async def get_trace_by_id(self, trace_id: str) -> Optional[Trace]:
        """
        Get a trace by ID.
        
        Args:
            trace_id: Trace ID
            
        Returns:
            Trace or None if not found
        """
        return self.db.query(Trace).filter(Trace.id == trace_id).first()
    
    async def get_last_sync_timestamp(self, project_id: str) -> Optional[datetime]:
        """
        Get the timestamp of the last synchronized trace.
        
        Args:
            project_id: Project ID
            
        Returns:
            Last sync timestamp or None
        """
        last_trace = (
            self.db.query(Trace)
            .filter(Trace.project_id == project_id)
            .order_by(desc(Trace.last_synced_at))
            .first()
        )
        
        if last_trace:
            return last_trace.last_synced_at
        return None
    
    def commit(self):
        """Commit the transaction."""
        self.db.commit()
    
    def rollback(self):
        """Rollback the transaction."""
        self.db.rollback()