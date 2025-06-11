from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
import logging
import time

from app.repositories.langfuse_repository import LangfuseRepository
from app.repositories.trace_repository import TraceRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.observation_repository import ObservationRepository
from app.schemas.trace import TraceCreate, ObservationCreate, TraceSyncStatus
from app.services.data_quality_service import DataQualityService

logger = logging.getLogger(__name__)


class TraceService:
    """Service for managing traces and synchronization with Langfuse."""

    @staticmethod
    async def sync_traces(
        project_id: str, user_id: str, db: Session
    ) -> TraceSyncStatus:
        """
        Sync traces from Langfuse for a specific project.

        Args:
            project_id: UUID of the project
            user_id: UUID of the requesting user
            db: Database session

        Returns:
            TraceSyncStatus with sync results
        """
        sync_started_at = datetime.utcnow()
        trace_repo = TraceRepository(db)
        project_repo = ProjectRepository(db)
        observation_repo = ObservationRepository(db)

        try:
            # Get project and verify user access
            project = await TraceService._get_project_with_access(
                project_id, user_id, project_repo
            )

            # Get Langfuse configuration
            langfuse_config = project.platform_config
            if not langfuse_config or project.platform_type != "langfuse":
                raise ValueError("Project is not configured for Langfuse")

            public_key = langfuse_config.get("public_key")
            secret_key = langfuse_config.get("secret_key")
            server_url = langfuse_config.get("url")

            if not all([public_key, secret_key, server_url]):
                raise ValueError("Incomplete Langfuse configuration")

            # Initialize Langfuse repository
            langfuse_repo = LangfuseRepository(
                public_key=public_key, secret_key=secret_key, server=server_url
            )

            # Determine sync range (differential sync)
            from_timestamp = await trace_repo.get_last_sync_timestamp(project_id)

            logger.info(
                f"Starting trace sync for project {project_id} from {from_timestamp}"
            )

            # Fetch all traces from Langfuse first
            all_langfuse_traces = []
            page = 1

            logger.info("Fetching all traces from Langfuse...")
            while True:
                langfuse_traces = langfuse_repo.get_traces(
                    from_timestamp=from_timestamp, page=page, limit=50
                )

                if not langfuse_traces:
                    break

                all_langfuse_traces.extend(langfuse_traces)

                # Check if there are more pages
                if len(langfuse_traces) < 50:
                    break
                page += 1

            logger.info(f"Fetched {len(all_langfuse_traces)} traces from Langfuse")

            # Now process and save all traces to database
            new_traces = 0
            updated_traces = 0

            for langfuse_trace_data in all_langfuse_traces:
                try:
                    # Check if trace already exists
                    existing_trace = await trace_repo.get_existing_trace(
                        project_id, langfuse_trace_data["id"], "langfuse"
                    )

                    if existing_trace:
                        # Update existing trace
                        await TraceService._update_trace_from_langfuse(
                            existing_trace, langfuse_trace_data, trace_repo
                        )
                        updated_traces += 1
                    else:
                        # Create new trace
                        await TraceService._create_trace_from_langfuse(
                            project_id,
                            langfuse_trace_data,
                            langfuse_repo,
                            trace_repo,
                            observation_repo,
                        )
                        new_traces += 1

                except Exception as e:
                    logger.error(
                        f"Failed to sync trace {langfuse_trace_data.get('id')}: {e}"
                    )
                    continue

            db.commit()
            sync_completed_at = datetime.utcnow()

            logger.info(
                f"Trace sync completed for project {project_id}: {new_traces} new, {updated_traces} updated"
            )

            return TraceSyncStatus(
                project_id=UUID(project_id),
                total_traces=new_traces + updated_traces,
                new_traces=new_traces,
                updated_traces=updated_traces,
                sync_started_at=sync_started_at,
                sync_completed_at=sync_completed_at,
            )

        except Exception as e:
            db.rollback()
            logger.error(f"Trace sync failed for project {project_id}: {e}")
            return TraceSyncStatus(
                project_id=UUID(project_id),
                total_traces=0,
                new_traces=0,
                updated_traces=0,
                sync_started_at=sync_started_at,
                error=str(e),
            )

    @staticmethod
    async def get_traces_by_project(
        project_id: str, user_id: str, db: Session, limit: int = 50, offset: int = 0
    ) -> List:
        """
        Get traces for a specific project.

        Args:
            project_id: UUID of the project
            user_id: UUID of the requesting user
            db: Database session
            limit: Number of traces to return
            offset: Number of traces to skip

        Returns:
            List of traces
        """
        trace_repo = TraceRepository(db)
        project_repo = ProjectRepository(db)

        # Verify user access to project
        await TraceService._get_project_with_access(project_id, user_id, project_repo)

        traces = await trace_repo.get_traces_by_project(project_id, limit, offset)
        return traces

    @staticmethod
    async def get_trace_with_observations(
        trace_id: str, user_id: str, db: Session
    ) -> Optional:
        """
        Get a single trace with its observations.

        Args:
            trace_id: UUID of the trace
            user_id: UUID of the requesting user
            db: Database session

        Returns:
            Trace with observations or None
        """
        trace_repo = TraceRepository(db)
        project_repo = ProjectRepository(db)

        trace = await trace_repo.get_trace_by_id(trace_id)
        if not trace:
            return None

        # Verify user access to project
        await TraceService._get_project_with_access(
            str(trace.project_id), user_id, project_repo
        )

        return trace

    @staticmethod
    async def _get_project_with_access(
        project_id: str, user_id: str, project_repo: ProjectRepository
    ):
        """Verify user has access to project."""
        # For now, just get the project - TODO: implement proper access control
        project = await project_repo.get_project_by_id_str(project_id)

        if not project:
            raise ValueError("Project not found")

        return project

    @staticmethod
    async def _create_trace_from_langfuse(
        project_id: str,
        langfuse_data: Dict[str, Any],
        langfuse_repo: LangfuseRepository,
        trace_repo: TraceRepository,
        observation_repo: ObservationRepository,
    ):
        """Create a new trace from Langfuse data using abstract model."""

        # Parse timestamps
        timestamp = datetime.fromisoformat(
            langfuse_data["timestamp"].replace("Z", "+00:00")
        )

        # Create trace data
        trace_data = {
            "project_id": UUID(project_id),
            "external_id": langfuse_data["id"],
            "platform_type": "langfuse",
            "timestamp": timestamp,
            "raw_data": langfuse_data,
            "last_synced_at": datetime.utcnow(),
        }

        trace = await trace_repo.create_trace(trace_data)

        # Fetch and create observations for this trace
        observations_created = []
        try:
            trace_detail = langfuse_repo.get_trace(langfuse_data["id"])
            observations = trace_detail.get("observations", [])
            for obs_data in observations:
                observation = await TraceService._create_observation_from_langfuse(
                    trace.id, obs_data, observation_repo
                )
                if observation:
                    observations_created.append(observation)
            time.sleep(2)
        except Exception as e:
            logger.warning(
                f"Failed to sync observations for trace {langfuse_data['id']}: {e}"
            )

        # Perform data quality analysis if observations were created
        if observations_created:
            try:
                quality_score, quality_issues = await DataQualityService.analyze_trace_data_quality(
                    trace, observations_created, trace_repo.db
                )
                
                # Update trace with quality metrics
                await DataQualityService.update_trace_quality_metrics(
                    str(trace.id), quality_score, quality_issues, trace_repo.db
                )
                
                logger.info(
                    f"Data quality analysis completed for trace {trace.id}: "
                    f"score={quality_score:.2f}, issues={len(quality_issues)}"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to perform data quality analysis for trace {trace.id}: {e}"
                )

        return trace

    @staticmethod
    async def _update_trace_from_langfuse(
        trace, langfuse_data: Dict[str, Any], trace_repo: TraceRepository
    ):
        """Update an existing trace with new Langfuse data using abstract model."""

        # Update trace fields
        update_data = {
            "raw_data": langfuse_data,
            "last_synced_at": datetime.utcnow(),
        }

        updated_trace = await trace_repo.update_trace(trace, update_data)
        
        # Re-run data quality analysis for updated trace
        try:
            # Get all observations for this trace
            observations = updated_trace.observations if hasattr(updated_trace, 'observations') else []
            
            if observations:
                quality_score, quality_issues = await DataQualityService.analyze_trace_data_quality(
                    updated_trace, observations, trace_repo.db
                )
                
                # Update trace with quality metrics
                await DataQualityService.update_trace_quality_metrics(
                    str(updated_trace.id), quality_score, quality_issues, trace_repo.db
                )
                
                logger.info(
                    f"Data quality re-analysis completed for updated trace {updated_trace.id}: "
                    f"score={quality_score:.2f}, issues={len(quality_issues)}"
                )
        except Exception as e:
            logger.warning(
                f"Failed to perform data quality re-analysis for updated trace {updated_trace.id}: {e}"
            )

        return updated_trace

    @staticmethod
    async def _create_observation_from_langfuse(
        trace_id: UUID,
        langfuse_data: Dict[str, Any],
        observation_repo: ObservationRepository,
    ):
        """Create an observation from Langfuse data using abstract model."""

        # Parse timestamps
        start_time = datetime.fromisoformat(
            langfuse_data["startTime"].replace("Z", "+00:00")
        )

        # Handle parent observation ID if present
        parent_observation_id = None
        if langfuse_data.get("parentObservationId"):
            # Find parent observation by external_id
            parent_obs = await observation_repo.get_parent_observation(
                trace_id, langfuse_data["parentObservationId"], "langfuse"
            )
            if parent_obs:
                parent_observation_id = parent_obs.id

        # Create observation data
        observation_data = {
            "trace_id": trace_id,
            "parent_observation_id": parent_observation_id,
            "external_id": langfuse_data["id"],
            "platform_type": "langfuse",
            "start_time": start_time,
            "raw_data": langfuse_data,
        }

        return await observation_repo.create_observation(observation_data)
