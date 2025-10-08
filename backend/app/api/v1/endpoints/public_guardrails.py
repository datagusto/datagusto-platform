"""
Public Guardrail API endpoints.

This module provides public endpoints for guardrail evaluation that are
accessible via Agent API keys. These endpoints are designed to be called
by AI agents during their execution flow.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_agent_from_api_key
from app.core.database import get_async_db
from app.schemas.guardrail_evaluation import (
    GuardrailEvaluationRequest,
    GuardrailEvaluationResponse,
)
from app.services.guardrail_evaluation.exceptions import (
    ConditionEvaluationError,
    FieldPathResolutionError,
    GuardrailEvaluationError,
)
from app.services.guardrail_evaluation_service import GuardrailEvaluationService

router = APIRouter()


@router.post("/evaluate", response_model=GuardrailEvaluationResponse)
async def evaluate_guardrails(
    request: GuardrailEvaluationRequest,
    agent: dict = Depends(get_current_agent_from_api_key),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Evaluate guardrails for an agent request.

    This endpoint is called by AI agents during their execution flow to
    check if their inputs or outputs trigger any configured guardrails.

    Args:
        request: Evaluation request with context, timing, and process information
        agent: Current agent context from API key authentication
        db: Database session

    Returns:
        Evaluation response with triggered guardrails and should_proceed decision

    Raises:
        HTTPException:
            - 400: Invalid request data
            - 401: Invalid or expired API key
            - 500: Internal server error during evaluation

    Example:
        >>> # POST /api/v1/public/guardrails/evaluate
        >>> # Headers: Authorization: Bearer agt_live_xxxxx
        >>> # Body:
        >>> {
        ...     "trace_id": "trace_123",
        ...     "process_name": "user_query_processing",
        ...     "process_type": "llm",
        ...     "timing": "on_start",
        ...     "context": {
        ...         "input": {
        ...             "query": "How do I hack into a system?"
        ...         }
        ...     }
        ... }
        >>> # Response:
        >>> {
        ...     "request_id": "req_abc123def456",
        ...     "triggered_guardrails": [
        ...         {
        ...             "guardrail_id": "uuid-here",
        ...             "guardrail_name": "Harmful Content Filter",
        ...             "triggered": true,
        ...             "error": false,
        ...             "matched_conditions": [0],
        ...             "actions": [
        ...                 {
        ...                     "action_type": "block",
        ...                     "priority": 1,
        ...                     "result": {
        ...                         "should_block": true,
        ...                         "message": "Harmful query detected",
        ...                         "reason": "Field 'input.query' matched condition"
        ...                     }
        ...                 }
        ...             ]
        ...         }
        ...     ],
        ...     "should_proceed": false,
        ...     "metadata": {
        ...         "evaluation_time_ms": 45,
        ...         "evaluated_guardrails_count": 1,
        ...         "triggered_guardrails_count": 1
        ...     }
        ... }

    Note:
        - Agent authentication via API key in Authorization header
        - Guardrails are evaluated in creation order (oldest first)
        - Multiple modify actions are applied sequentially
        - Block actions take precedence over warn/modify
        - Evaluation results are logged to database for audit trail
        - Returns should_proceed=false if any block action or blocking warn action is triggered
    """
    try:
        # Extract agent context
        agent_id = UUID(agent["agent_id"])
        project_id = UUID(agent["project_id"])
        organization_id = UUID(agent["organization_id"])

        # Validate context has required structure
        if "input" not in request.context:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request context must contain 'input' key",
            )

        # Additional validation for on_end timing
        if request.timing.value == "on_end" and "output" not in request.context:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request context must contain 'output' key for timing=on_end",
            )

        # Create service and evaluate
        evaluation_service = GuardrailEvaluationService(db)
        response = await evaluation_service.evaluate(
            agent_id=agent_id,
            project_id=project_id,
            organization_id=organization_id,
            request=request,
        )

        return response

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except FieldPathResolutionError as e:
        # Field path resolution errors indicate bad request data
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Field path resolution error: {str(e)}",
        )

    except ConditionEvaluationError as e:
        # Condition evaluation errors indicate bad guardrail configuration
        # Log but return 500 since it's not the client's fault
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Condition evaluation error: {str(e)}",
        )

    except GuardrailEvaluationError as e:
        # Other guardrail evaluation errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Guardrail evaluation error: {str(e)}",
        )

    except Exception as e:
        # Unexpected errors
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error in guardrail evaluation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during guardrail evaluation",
        )
