"""
Secure API endpoints requiring agent API key authentication.

This module provides endpoints accessible via Agent API keys for operations
like tool registration and other agent-specific functionality.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_agent_from_api_key
from app.core.database import get_async_db
from app.schemas.safety import (
    AlignmentRequest,
    AlignmentResponse,
    SessionValidationRequest,
)
from app.schemas.tool_definition import (
    ToolRegistrationRequest,
    ToolRegistrationResponse,
)
from app.services.safety_service import SafetyService
from app.services.tool_definition_service import ToolDefinitionService

router = APIRouter()


@router.post("/tools/register", response_model=ToolRegistrationResponse)
async def register_tools(
    request: ToolRegistrationRequest,
    agent: dict = Depends(get_current_agent_from_api_key),
    db: AsyncSession = Depends(get_async_db),
) -> Any:
    """
    Register AI agent tool definitions.

    Creates a new revision of tool definitions for the authenticated agent.
    Each registration creates a new revision while preserving full history,
    enabling complete traceability for guardrail generation and compliance.

    Args:
        request: Tool registration request with tools list
        agent: Current agent context from API key authentication
        db: Database session

    Returns:
        Registration response with revision information

    Raises:
        HTTPException:
            - 400: Invalid request data
            - 401: Invalid or expired API key
            - 500: Internal server error during registration

    Example:
        >>> # POST /api/v1/public/tools/register
        >>> # Headers: Authorization: Bearer agt_live_xxxxx
        >>> # Body:
        >>> {
        ...     "tools": [
        ...         {
        ...             "name": "get_weather",
        ...             "description": "Get current weather information",
        ...             "input_schema": {
        ...                 "type": "object",
        ...                 "properties": {
        ...                     "location": {"type": "string"}
        ...                 },
        ...                 "required": ["location"]
        ...             },
        ...             "output_schema": {
        ...                 "type": "object",
        ...                 "properties": {
        ...                     "temperature": {"type": "number"},
        ...                     "condition": {"type": "string"}
        ...                 }
        ...             }
        ...         }
        ...     ]
        ... }
        >>> # Response:
        >>> {
        ...     "tool_definition_id": "uuid-here",
        ...     "revision_id": "uuid-here",
        ...     "agent_id": "uuid-here",
        ...     "tools_count": 1,
        ...     "previous_revision_id": null,
        ...     "created_at": "2025-11-18T16:30:00Z"
        ... }

    Note:
        - Agent authentication via API key in Authorization header
        - No validation is performed on tool definitions (stored as-is)
        - Each call creates a new revision, preserving full history
        - Previous revisions remain accessible for audit and rollback
        - Tool definitions are tracked by agent_id for complete traceability
    """
    try:
        # Extract agent context from API key
        agent_id = UUID(agent["agent_id"])

        # Create service and register tools
        service = ToolDefinitionService(db)
        response = await service.register_tools(agent_id=agent_id, request=request)

        return response

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        # Log unexpected errors
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error in tool registration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during tool registration",
        )


@router.post("/sessions/alignment")
async def alignment_session(
    request: AlignmentRequest,
    agent: dict = Depends(get_current_agent_from_api_key),
    db: AsyncSession = Depends(get_async_db),
):
    """Align a session

    1. Extract keywords from user instruction
    2. Disambiguate keywords
    3. Generate tool invocation rules
    """

    service = SafetyService(db)

    session_id, key_terms_output, _ = await service.alignment_session(
        agent_id=agent["agent_id"],
        session_id=request.session_id,
        user_instruction=request.user_instruction,
    )

    return AlignmentResponse(
        session_id=session_id,
        key_terms=key_terms_output.key_terms,
    )


@router.post("/sessions/validate")
async def validate_session(
    request: SessionValidationRequest,
    agent: dict = Depends(get_current_agent_from_api_key),
    db: AsyncSession = Depends(get_async_db),
) -> dict[str, Any]:
    """
    Validate tool/LLM invocation against session-generated guardrails.

    This endpoint evaluates a process invocation (tool call, LLM call, etc.)
    against guardrails that were generated during the session alignment phase.
    It reuses the exact same evaluation logic as the guardrail evaluation service.

    Args:
        request: Validation request with session_id, process details, and context
        agent: Current agent context from API key authentication
        db: Database session

    Returns:
        Validation response with should_proceed, triggered_guardrails, and metadata

    Raises:
        HTTPException:
            - 400: Invalid request data
            - 401: Invalid or expired API key
            - 404: Session not found
            - 500: Internal server error during validation

    Example:
        >>> # POST /api/v1/public/sessions/validate
        >>> # Headers: Authorization: Bearer agt_live_xxxxx
        >>> # Body:
        >>> {
        ...     "session_id": "123e4567-e89b-12d3-a456-426614174000",
        ...     "trace_id": "trace_abc123",
        ...     "process_name": "get_exam_results",
        ...     "process_type": "tool",
        ...     "timing": "on_start",
        ...     "context": {
        ...         "input": {
        ...             "semester": "spring",
        ...             "year": 2024
        ...         }
        ...     }
        ... }
        >>> # Response:
        >>> {
        ...     "should_proceed": true,
        ...     "triggered_guardrails": [...],
        ...     "metadata": {
        ...         "evaluation_time_ms": 45,
        ...         "evaluated_guardrails_count": 3,
        ...         "triggered_guardrails_count": 1
        ...     }
        ... }

    Note:
        - Agent authentication via API key in Authorization header
        - session_id must reference a session created via POST /sessions/alignment
        - Validation results are automatically saved to session_validation_logs table
        - Results are displayed in frontend Validation History section
    """
    try:
        # Extract agent context from API key
        agent_id = UUID(agent["agent_id"])
        project_id = UUID(agent["project_id"])
        organization_id = UUID(agent["organization_id"])

        # Convert session_id from string to UUID
        session_id = UUID(request.session_id)

        # Create service and validate
        service = SafetyService(db)
        (
            should_proceed,
            triggered_guardrails,
            metadata,
        ) = await service.validate_session_guardrails(
            session_id=session_id,
            agent_id=agent_id,
            project_id=project_id,
            organization_id=organization_id,
            trace_id=request.trace_id,
            process_name=request.process_name,
            process_type=request.process_type.value,
            timing=request.timing.value,
            context=request.context,
        )

        return {
            "should_proceed": should_proceed,
            "triggered_guardrails": [
                tg.model_dump(mode="json") for tg in triggered_guardrails
            ],
            "metadata": metadata,
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except ValueError as e:
        # Handle UUID conversion errors
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Invalid UUID in request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UUID format: {str(e)}",
        )

    except Exception as e:
        # Log unexpected errors
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error in session validation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during session validation",
        )
