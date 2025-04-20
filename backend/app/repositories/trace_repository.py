from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from sqlalchemy import select
import uuid

from app.models.trace import Trace as TraceModel, TraceStatus
from app.models.observation import Observation as ObservationModel


class TraceRepository:
    """Repository for trace operations."""

    def __init__(self, db: Session):
        self.db = db

    async def create_trace(self, trace_data: Dict[str, Any]) -> TraceModel:
        """
        Create a new trace.

        Args:
            trace_data: Trace data

        Returns:
            Created trace
        """
        trace = TraceModel(**trace_data)
        self.db.add(trace)
        self.db.commit()
        self.db.refresh(trace)
        return trace

    async def get_trace_by_id(self, trace_id: str) -> Optional[TraceModel]:
        """
        Get a trace by ID.

        Args:
            trace_id: Trace ID

        Returns:
            Trace or None
        """
        return self.db.query(TraceModel).filter(TraceModel.id == trace_id).first()

    async def get_traces_by_agent_id(self, agent_id: str) -> List[TraceModel]:
        """
        Get all traces for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            List of traces
        """
        return (
            self.db.query(TraceModel)
            .filter(TraceModel.agent_id == agent_id)
            .order_by(TraceModel.timestamp.desc())
            .all()
        )

    async def get_latest_trace_by_agent_id(self, agent_id: str) -> Optional[TraceModel]:
        """
        Get the latest trace for an agent.
        """
        return (
            self.db.query(TraceModel)
            .filter(TraceModel.agent_id == agent_id)
            .order_by(TraceModel.timestamp.desc())
            .first()
        )

    async def update_trace(
        self, trace_id: str, trace_data: Dict[str, Any]
    ) -> Optional[TraceModel]:
        """
        Update a trace.

        Args:
            trace_id: Trace ID
            trace_data: Trace data to update

        Returns:
            Updated trace or None
        """
        trace = await self.get_trace_by_id(trace_id)
        if not trace:
            return None

        for key, value in trace_data.items():
            setattr(trace, key, value)

        self.db.commit()
        self.db.refresh(trace)
        return trace

    async def delete_trace(self, trace_id: str) -> bool:
        """
        Delete a trace.

        Args:
            trace_id: Trace ID

        Returns:
            True if deleted
        """
        trace = await self.get_trace_by_id(trace_id)
        if not trace:
            return False

        self.db.delete(trace)
        self.db.commit()
        return True

    async def add_observation(
        self, observation_data: Dict[str, Any]
    ) -> ObservationModel:
        """
        Add an observation to a trace.

        Args:
            observation_data: Observation data

        Returns:
            Created observation
        """
        observation = ObservationModel(**observation_data)
        self.db.add(observation)
        self.db.commit()
        self.db.refresh(observation)
        return observation

    async def get_observations_by_trace_id(
        self, trace_id: str
    ) -> List[ObservationModel]:
        """
        Get all observations for a trace.

        Args:
            trace_id: Trace ID

        Returns:
            List of observations
        """
        return (
            self.db.query(ObservationModel)
            .filter(ObservationModel.trace_id == trace_id)
            .order_by(ObservationModel.start_time.asc())
            .all()
        )
