"""
Guardrail Evaluation Service for orchestrating guardrail evaluation.

This service coordinates all components of guardrail evaluation including:
- Fetching active guardrails for an agent
- Evaluating conditions
- Executing actions
- Calculating should_proceed
- Saving evaluation logs
"""

import logging
import time
import uuid
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guardrail import (
    Guardrail,
    GuardrailActiveStatus,
    GuardrailAgentAssignment,
    GuardrailArchive,
)
from app.repositories.guardrail_evaluation_log_repository import (
    GuardrailEvaluationLogRepository,
)
from app.schemas.guardrail_evaluation import (
    ActionResult,
    EvaluationMetadata,
    GuardrailEvaluationRequest,
    GuardrailEvaluationResponse,
    TriggeredGuardrail,
)
from app.services.guardrail_evaluation.action_executor import (
    execute_block_action,
    execute_modify_action,
    execute_warn_action,
)
from app.services.guardrail_evaluation.condition_evaluator import evaluate_conditions
from app.services.guardrail_evaluation.exceptions import (
    ConditionEvaluationError,
    FieldPathResolutionError,
)
from app.services.guardrail_evaluation.should_proceed_calculator import (
    calculate_should_proceed_with_configs,
)

logger = logging.getLogger(__name__)


class GuardrailEvaluationService:
    """Service for handling guardrail evaluation operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the guardrail evaluation service.

        Args:
            db: Async database session
        """
        self.db = db
        self.log_repo = GuardrailEvaluationLogRepository(db)

    async def get_active_guardrails_for_agent(
        self, agent_id: UUID, timing: str, process_type: str
    ) -> list[Guardrail]:
        """
        Get active guardrails assigned to an agent, filtered by timing and process_type.

        Args:
            agent_id: Agent UUID
            timing: "on_start" or "on_end"
            process_type: "llm", "tool", "retrieval", or "agent"

        Returns:
            List of active, non-archived guardrails matching criteria

        Example:
            >>> guardrails = await service.get_active_guardrails_for_agent(
            ...     agent_id, "on_start", "tool"
            ... )
        """
        # Query for assigned, active, non-archived guardrails
        stmt = (
            select(Guardrail)
            .join(
                GuardrailAgentAssignment,
                Guardrail.id == GuardrailAgentAssignment.guardrail_id,
            )
            .join(
                GuardrailActiveStatus,
                Guardrail.id == GuardrailActiveStatus.guardrail_id,
            )
            .outerjoin(GuardrailArchive, Guardrail.id == GuardrailArchive.guardrail_id)
            .where(
                GuardrailAgentAssignment.agent_id == agent_id,
                GuardrailArchive.guardrail_id.is_(None),  # Not archived
            )
            .order_by(Guardrail.created_at.asc())  # Oldest first for consistent order
        )

        result = await self.db.execute(stmt)
        all_guardrails = result.scalars().all()

        # Filter by timing in definition
        filtered_guardrails = []
        for guardrail in all_guardrails:
            definition = guardrail.definition
            trigger = definition.get("trigger", {})
            trigger_type = trigger.get("type")

            if trigger_type == timing:
                filtered_guardrails.append(guardrail)

        logger.info(
            f"Found {len(filtered_guardrails)} active guardrails for agent {agent_id} "
            f"(timing={timing}, process_type={process_type})"
        )

        return filtered_guardrails

    async def evaluate(
        self,
        agent_id: UUID,
        project_id: UUID,
        organization_id: UUID,
        request: GuardrailEvaluationRequest,
    ) -> GuardrailEvaluationResponse:
        """
        Evaluate guardrails for a request.

        This is the main evaluation orchestration method.

        Args:
            agent_id: Agent making the request
            project_id: Project the agent belongs to
            organization_id: Organization (for logging)
            request: Evaluation request

        Returns:
            Evaluation response with results

        Example:
            >>> response = await service.evaluate(
            ...     agent_id, project_id, org_id, request
            ... )
            >>> print(response.should_proceed)
        """
        start_time = time.time()

        # Generate unique request ID
        request_id = f"req_{uuid.uuid4().hex[:12]}"

        logger.info(
            f"Starting evaluation {request_id} for agent {agent_id}, "
            f"process={request.process_name}, timing={request.timing.value}"
        )

        # Get active guardrails
        guardrails = await self.get_active_guardrails_for_agent(
            agent_id, request.timing.value, request.process_type.value
        )

        triggered_guardrails_list: list[TriggeredGuardrail] = []
        guardrail_definitions: dict[str, dict[str, Any]] = {}

        # Evaluate each guardrail
        for guardrail in guardrails:
            guardrail_definitions[str(guardrail.id)] = guardrail.definition

            triggered_result = await self._evaluate_guardrail(
                guardrail, request.context
            )

            triggered_guardrails_list.append(triggered_result)

        # Calculate should_proceed
        should_proceed = calculate_should_proceed_with_configs(
            [tg.model_dump() for tg in triggered_guardrails_list], guardrail_definitions
        )

        # Calculate evaluation time
        evaluation_time_ms = int((time.time() - start_time) * 1000)

        # Count triggered guardrails (exclude ignored and error cases)
        triggered_count = sum(
            1
            for tg in triggered_guardrails_list
            if tg.triggered and not tg.ignored and not tg.error
        )

        # Count ignored guardrails
        ignored_count = sum(1 for tg in triggered_guardrails_list if tg.ignored)

        # Evaluated count excludes ignored guardrails
        evaluated_count = len(guardrails) - ignored_count

        metadata = EvaluationMetadata(
            evaluation_time_ms=evaluation_time_ms,
            evaluated_guardrails_count=evaluated_count,
            triggered_guardrails_count=triggered_count,
            ignored_guardrails_count=ignored_count,
        )

        response = GuardrailEvaluationResponse(
            request_id=request_id,
            triggered_guardrails=triggered_guardrails_list,
            should_proceed=should_proceed,
            metadata=metadata,
        )

        # Save evaluation log
        try:
            await self.save_evaluation_log(
                request_id=request_id,
                agent_id=agent_id,
                project_id=project_id,
                organization_id=organization_id,
                trace_id=request.trace_id,
                timing=request.timing.value,
                process_type=request.process_type.value,
                process_name=request.process_name,
                context=request.context,
                should_proceed=should_proceed,
                triggered_guardrails=triggered_guardrails_list,
                metadata=metadata,
                evaluation_time_ms=evaluation_time_ms,
                evaluated_guardrail_ids=[str(g.id) for g in guardrails],
            )
            logger.debug(f"Successfully saved evaluation log {request_id}")
        except Exception as e:
            logger.error(f"Failed to save evaluation log: {str(e)}", exc_info=True)
            # Don't fail the request if logging fails

        logger.info(
            f"Evaluation {request_id} completed: should_proceed={should_proceed}, "
            f"triggered={triggered_count}/{len(guardrails)}, time={evaluation_time_ms}ms"
        )

        return response

    async def _evaluate_guardrail(
        self, guardrail: Guardrail, context: dict[str, Any]
    ) -> TriggeredGuardrail:
        """
        Evaluate a single guardrail.

        Args:
            guardrail: Guardrail to evaluate
            context: Evaluation context

        Returns:
            TriggeredGuardrail result
        """
        try:
            definition = guardrail.definition
            trigger = definition.get("trigger", {})
            conditions = trigger.get("conditions", [])
            logic = trigger.get("logic", "and")

            # Evaluate conditions
            triggered, matched_indices = evaluate_conditions(context, conditions, logic)

            if not triggered:
                # Not triggered
                return TriggeredGuardrail(
                    guardrail_id=guardrail.id,
                    guardrail_name=guardrail.name,
                    triggered=False,
                    ignored=False,
                    error=False,
                    matched_conditions=[],
                    actions=[],
                )

            # Execute actions
            actions_config = definition.get("actions", [])
            action_results: list[ActionResult] = []

            for action_config in actions_config:
                action_type = action_config.get("type")

                try:
                    if action_type == "block":
                        result = execute_block_action(
                            action_config, context, matched_indices, conditions
                        )
                    elif action_type == "warn":
                        result = execute_warn_action(action_config)
                    elif action_type == "modify":
                        result = execute_modify_action(action_config, context)
                    else:
                        logger.warning(f"Unknown action type: {action_type}")
                        continue

                    action_results.append(ActionResult(**result))

                except Exception as e:
                    logger.error(f"Action execution error: {str(e)}")
                    # Continue with other actions

            return TriggeredGuardrail(
                guardrail_id=guardrail.id,
                guardrail_name=guardrail.name,
                triggered=True,
                ignored=False,
                error=False,
                matched_conditions=matched_indices,
                actions=action_results,
            )

        except (FieldPathResolutionError, ConditionEvaluationError) as e:
            # Known evaluation errors - these are ignored (field not found, parse errors, etc.)
            logger.warning(
                f"Guardrail '{guardrail.name}' ignored due to evaluation issue: {str(e)}"
            )
            return TriggeredGuardrail(
                guardrail_id=guardrail.id,
                guardrail_name=guardrail.name,
                triggered=False,
                ignored=True,
                ignored_reason=str(e),
                error=False,
                matched_conditions=[],
                actions=[],
            )

        except Exception as e:
            # Unexpected system errors
            logger.error(
                f"Unexpected error evaluating guardrail {guardrail.name}: {str(e)}"
            )
            return TriggeredGuardrail(
                guardrail_id=guardrail.id,
                guardrail_name=guardrail.name,
                triggered=False,
                ignored=False,
                error=True,
                error_message=f"Unexpected error: {str(e)}",
                matched_conditions=[],
                actions=[],
            )

    async def save_evaluation_log(
        self,
        request_id: str,
        agent_id: UUID,
        project_id: UUID,
        organization_id: UUID,
        trace_id: str | None,
        timing: str,
        process_type: str,
        process_name: str,
        context: dict[str, Any],
        should_proceed: bool,
        triggered_guardrails: list[TriggeredGuardrail],
        metadata: EvaluationMetadata,
        evaluation_time_ms: int,
        evaluated_guardrail_ids: list[str],
    ) -> None:
        """
        Save evaluation log to database.

        Args:
            request_id: Unique request ID
            agent_id: Agent UUID
            project_id: Project UUID
            organization_id: Organization UUID
            trace_id: Optional external trace ID
            timing: Evaluation timing
            process_type: Process type
            process_name: Process name
            context: Evaluation context
            should_proceed: Final decision
            triggered_guardrails: List of triggered guardrails
            metadata: Evaluation metadata
            evaluation_time_ms: Evaluation time
            evaluated_guardrail_ids: List of evaluated guardrail IDs
        """
        log_data = {
            "process_name": process_name,
            "request_context": context,
            "evaluated_guardrail_ids": evaluated_guardrail_ids,
            "triggered_guardrail_ids": [
                str(tg.guardrail_id)
                for tg in triggered_guardrails
                if tg.triggered and not tg.ignored and not tg.error
            ],
            "ignored_guardrail_ids": [
                str(tg.guardrail_id) for tg in triggered_guardrails if tg.ignored
            ],
            "evaluation_result": {
                "triggered_guardrails": [
                    tg.model_dump(mode="json") for tg in triggered_guardrails
                ],
                "metadata": metadata.model_dump(mode="json"),
            },
            "evaluation_time_ms": evaluation_time_ms,
        }

        await self.log_repo.create(
            {
                "request_id": request_id,
                "agent_id": agent_id,
                "project_id": project_id,
                "organization_id": organization_id,
                "trace_id": trace_id,
                "timing": timing,
                "process_type": process_type,
                "should_proceed": should_proceed,
                "log_data": log_data,
            }
        )

        await self.db.commit()
        logger.debug(f"Saved evaluation log {request_id}")


__all__ = ["GuardrailEvaluationService"]
