import os
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from sqlalchemy import text
import json

from app.models.trace import Trace as TraceModel, TraceStatus
from app.models.observation import Observation as ObservationModel
from app.repositories.trace_repository import TraceRepository
from app.repositories.agent_repository import AgentRepository
from app.repositories.organization_member_repository import OrganizationMemberRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.langfuse_repository import LangfuseRepository
from app.services.evaluation_service import evaluate_trace


class TraceService:
    """Service for trace operations."""

    @staticmethod
    async def create_trace(
        agent_id: str, user_id: str, trace_data: Dict[str, Any], db: Session
    ) -> TraceModel:
        """
        Create a new trace.

        Args:
            agent_id: Agent ID
            user_id: User ID
            trace_data: Trace data
            db: Database session

        Returns:
            Created trace
        """
        try:
            # Initialize repositories
            agent_repo = AgentRepository(db)
            trace_repo = TraceRepository(db)

            # Get agent
            agent = await agent_repo.get_agent_by_id(agent_id)

            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
                )

            # Check if user is a member of the agent's organization
            member_repo = OrganizationMemberRepository(db)
            member = await member_repo.get_member(user_id, agent.organization_id)

            if not member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to create traces for this agent",
                )

            # Create trace
            trace_data_with_defaults = {
                "agent_id": agent_id,
                "status": TraceStatus.COMPLETED,
                **trace_data,
            }

            # Convert metadata to trace_metadata if it exists
            if "metadata" in trace_data_with_defaults:
                trace_data_with_defaults["trace_metadata"] = (
                    trace_data_with_defaults.pop("metadata")
                )

            trace = await trace_repo.create_trace(trace_data_with_defaults)
            return trace
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create trace: {str(e)}",
            )

    @staticmethod
    async def get_trace(trace_id: str, user_id: str, db: Session) -> TraceModel:
        """
        Get a trace by ID.

        Args:
            trace_id: Trace ID
            user_id: User ID
            db: Database session

        Returns:
            Trace
        """
        try:
            # Initialize repositories
            trace_repo = TraceRepository(db)

            # Get trace
            trace = await trace_repo.get_trace_by_id(trace_id)

            if not trace:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found"
                )

            # Get agent to check organization
            agent_repo = AgentRepository(db)
            agent = await agent_repo.get_agent_by_id(trace.agent_id)

            # Check if user is a member of the agent's organization
            member_repo = OrganizationMemberRepository(db)
            member = await member_repo.get_member(user_id, agent.organization_id)

            if not member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to access this trace",
                )

            return trace
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get trace: {str(e)}",
            )

    @staticmethod
    async def get_traces_by_agent(
        agent_id: str, user_id: str, db: Session
    ) -> List[TraceModel]:
        """
        Get all traces for an agent.

        Args:
            agent_id: Agent ID
            user_id: User ID
            db: Database session

        Returns:
            List of traces
        """
        try:
            # Initialize repositories
            agent_repo = AgentRepository(db)
            trace_repo = TraceRepository(db)

            # Get agent
            agent = await agent_repo.get_agent_by_id(agent_id)

            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
                )

            # Check if user is a member of the agent's organization
            member_repo = OrganizationMemberRepository(db)
            member = await member_repo.get_member(user_id, agent.organization_id)

            if not member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to access traces for this agent",
                )

            # Get traces
            traces = await trace_repo.get_traces_by_agent_id(agent_id)
            return traces
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get traces: {str(e)}",
            )

    @staticmethod
    async def update_trace(
        trace_id: str, user_id: str, trace_data: Dict[str, Any], db: Session
    ) -> TraceModel:
        """
        Update a trace.

        Args:
            trace_id: Trace ID
            user_id: User ID
            trace_data: Trace data to update
            db: Database session

        Returns:
            Updated trace
        """
        try:
            # Initialize repositories
            trace_repo = TraceRepository(db)

            # Get trace
            trace = await trace_repo.get_trace_by_id(trace_id)

            if not trace:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found"
                )

            # Get agent to check organization
            agent_repo = AgentRepository(db)
            agent = await agent_repo.get_agent_by_id(trace.agent_id)

            # Check if user is a member of the agent's organization
            member_repo = OrganizationMemberRepository(db)
            member = await member_repo.get_member(user_id, agent.organization_id)

            if not member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to update this trace",
                )

            # Convert metadata to trace_metadata if it exists
            if "metadata" in trace_data:
                trace_data["trace_metadata"] = trace_data.pop("metadata")

            # Update trace
            updated_trace = await trace_repo.update_trace(trace_id, trace_data)
            return updated_trace
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update trace: {str(e)}",
            )

    @staticmethod
    async def add_observation(
        trace_id: str, user_id: str, observation_data: Dict[str, Any], db: Session
    ) -> ObservationModel:
        """
        Add an observation to a trace.

        Args:
            trace_id: Trace ID
            user_id: User ID
            observation_data: Observation data
            db: Database session

        Returns:
            Created observation
        """
        try:
            # Initialize repositories
            trace_repo = TraceRepository(db)

            # Get trace
            trace = await trace_repo.get_trace_by_id(trace_id)

            if not trace:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found"
                )

            # Get agent to check organization
            agent_repo = AgentRepository(db)
            agent = await agent_repo.get_agent_by_id(trace.agent_id)

            # Check if user is a member of the agent's organization
            member_repo = OrganizationMemberRepository(db)
            member = await member_repo.get_member(user_id, agent.organization_id)

            if not member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to add observations to this trace",
                )

            # Add trace_id to observation data
            observation_data["trace_id"] = trace_id

            # Convert metadata to observation_metadata if it exists
            if "metadata" in observation_data:
                observation_data["observation_metadata"] = observation_data.pop(
                    "metadata"
                )

            # Add observation
            observation = await trace_repo.add_observation(observation_data)
            return observation
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add observation: {str(e)}",
            )

    @staticmethod
    async def get_trace_with_observations(
        trace_id: str, user_id: str, db: Session
    ) -> Dict[str, Any]:
        """
        Get a trace with its observations.

        Args:
            trace_id: Trace ID
            user_id: User ID
            db: Database session

        Returns:
            Trace with observations
        """
        try:
            # Initialize repositories
            trace_repo = TraceRepository(db)

            # Get trace
            trace = await trace_repo.get_trace_by_id(trace_id)

            if not trace:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found"
                )

            # Get agent to check organization
            agent_repo = AgentRepository(db)
            agent = await agent_repo.get_agent_by_id(trace.agent_id)

            # Check if user is a member of the agent's organization
            member_repo = OrganizationMemberRepository(db)
            member = await member_repo.get_member(user_id, agent.organization_id)

            if not member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to access this trace",
                )

            # Get observations
            observations = await trace_repo.get_observations_by_trace_id(trace_id)

            # Return trace with observations
            return {"trace": trace, "observations": observations}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get trace with observations: {str(e)}",
            )

    @staticmethod
    async def get_traces_for_user(user_id: str, db: Session) -> List[TraceModel]:
        """
        Get all traces for a user across all agents created by the user.

        Args:
            user_id: User ID
            db: Database session

        Returns:
            List of traces
        """
        try:
            # Initialize repositories
            trace_repo = TraceRepository(db)

            # Use direct SQL query to get all traces for agents created by the user
            query = text("""
                SELECT t.* FROM traces t
                JOIN agents a ON t.agent_id = a.id
                WHERE a.creator_id = :user_id
                ORDER BY t.timestamp DESC
            """)

            print(f"Executing query for user_id: {user_id}")
            print(f"SQL query: {query}")

            # Execute the query synchronously (no await)
            result = db.execute(query, {"user_id": user_id})
            traces = result.mappings().all()

            # Convert the raw SQL results to Trace models
            trace_models = []
            for trace_data in traces:
                try:
                    # Convert SQLAlchemy RowMapping to dict
                    trace_dict = dict(trace_data)
                    trace_model = TraceModel()

                    # Manually set attributes to handle any type conversions
                    for key, value in trace_dict.items():
                        if hasattr(trace_model, key):
                            setattr(trace_model, key, value)

                    trace_models.append(trace_model)
                except Exception as model_error:
                    print(
                        f"Error creating trace model from data: {trace_data}, error: {str(model_error)}"
                    )
                    # Continue processing other traces even if one fails
                    continue

            return trace_models
        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            print(f"Error in get_traces_for_user: {str(e)}\n{error_details}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get traces: {str(e)}",
            )

    @staticmethod
    async def sync_traces(agent_id: str, user_id: str, db: Session) -> bool:
        """
        Sync traces for an agent.
        """
        try:
            # Initialize repositories
            agent_repo = AgentRepository(db)

            # Get agent
            agent = await agent_repo.get_agent_by_id(agent_id)

            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
                )

            trace_repo = TraceRepository(db)
            latest_trace = await trace_repo.get_latest_trace_by_agent_id(agent_id)
            latest_trace_timestamp = latest_trace.timestamp if latest_trace else None

            if not agent.observability_config:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Agent does not have observability config",
                )

            if agent.observability_config["platform_type"] == "langfuse":
                langfuse_repo = LangfuseRepository(
                    agent.observability_config["auth"]["public_key"],
                    agent.observability_config["auth"]["secret_key"],
                    agent.observability_config["auth"]["server"],
                )
                traces = langfuse_repo.get_traces(latest_trace_timestamp)
                for t in sorted(traces, key=lambda x: x["timestamp"]):
                    trace = langfuse_repo.get_trace(t["id"])
                    # Create trace
                    trace_data = {
                        "agent_id": agent_id,
                        "observability_id": trace["id"],
                        "name": trace["name"],
                        "timestamp": trace["timestamp"],
                        "input": json.dumps(trace["input"]),
                        "output": json.dumps(trace["output"]),
                        "latency": trace["latency"],
                        "total_cost": trace["totalCost"],
                        "created_at": trace["createdAt"],
                        "updated_at": trace["updatedAt"],
                    }

                    trace_db = await trace_repo.create_trace(trace_data)

                    # Create observations
                    for o in trace["observations"]:
                        print(o)
                        observation_data = {
                            "trace_id": trace_db.id,
                            "observability_id": o["id"],
                            "type": o["type"],
                            "parent_observation_id": o["parentObservationId"],
                            "name": o["name"],
                            "start_time": o["startTime"],
                            "end_time": o["endTime"],
                            "input": json.dumps(o["input"]),
                            "output": json.dumps(o["output"]),
                            "model_parameters": o["modelParameters"],
                            "created_at": o["createdAt"],
                            "updated_at": o["updatedAt"],
                            "usage_details": o["usageDetails"],
                            "cost_details": o["costDetails"],
                            "model": o["model"],
                            "latency": o["latency"],
                            # "observation_metadata": o["metadata"],
                            "usage": o["usage"],
                        }

                        await trace_repo.add_observation(observation_data)

                    # evaluate the trace
                    if os.getenv("OPENAI_API_KEY", None) is not None:
                        evaluation_results = evaluate_trace(trace)
                        await trace_repo.update_trace(
                            trace_db.id, {"evaluation_results": evaluation_results}
                        )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Unsupported observability platform",
                )

        except HTTPException as e:
            raise e
