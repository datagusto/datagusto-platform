"""
Session service for managing session and alignment history operations.

This service handles session-related operations including CRUD operations,
alignment history management, and session lifecycle management.
"""

from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.agent_repository import AgentRepository
from app.repositories.session_alignment_history_repository import (
    SessionAlignmentHistoryRepository,
)
from app.repositories.session_repository import SessionRepository
from app.repositories.session_validation_log_repository import (
    SessionValidationLogRepository,
)


class SessionService:
    """Service for handling session and alignment history operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the session service.

        Args:
            db: Async database session
        """
        self.db = db
        self.session_repo = SessionRepository(db)
        self.history_repo = SessionAlignmentHistoryRepository(db)
        self.agent_repo = AgentRepository(db)
        self.validation_log_repo = SessionValidationLogRepository(db)

    async def create_session(self, agent_id: UUID) -> dict[str, Any]:
        """
        Create a new session.

        Automatically derives project_id and organization_id from agent.

        Args:
            agent_id: Agent UUID

        Returns:
            Created session data

        Raises:
            HTTPException: If creation fails or agent not found
        """
        try:
            # Get agent to extract project_id and organization_id
            agent = await self.agent_repo.get_by_id(agent_id)
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Agent not found",
                )

            # Create session
            session = await self.session_repo.create(
                {
                    "agent_id": agent_id,
                    "project_id": agent.project_id,
                    "organization_id": agent.organization_id,
                    "status": "active",
                }
            )

            await self.db.commit()

            return await self.get_session(session.id)

        except HTTPException:
            await self.db.rollback()
            raise

        except IntegrityError as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Session creation failed: {str(e)}",
            )

        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating session: {str(e)}",
            )

    async def get_session(self, session_id: UUID) -> dict[str, Any]:
        """
        Get session by ID.

        Args:
            session_id: Session UUID

        Returns:
            Dictionary containing session data

        Raises:
            HTTPException: If session not found
        """
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        # Get alignment history count
        alignment_history_count = await self.history_repo.count_by_session(session.id)

        return {
            "id": str(session.id),
            "agent_id": str(session.agent_id),
            "project_id": str(session.project_id),
            "organization_id": str(session.organization_id),
            "status": session.status,
            "created_at": session.created_at.isoformat()
            if session.created_at
            else None,
            "updated_at": session.updated_at.isoformat()
            if session.updated_at
            else None,
            "alignment_history_count": alignment_history_count,
        }

    async def list_sessions(
        self,
        agent_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> dict[str, Any]:
        """
        List sessions for an agent with pagination and filtering.

        Args:
            agent_id: Agent UUID
            page: Page number (1-indexed)
            page_size: Number of items per page
            status: Filter by status

        Returns:
            Dictionary with items, total, page, page_size
        """
        sessions, total = await self.session_repo.get_by_agent(
            agent_id=agent_id,
            page=page,
            page_size=page_size,
            status=status,
        )

        items = []
        for session in sessions:
            alignment_history_count = await self.history_repo.count_by_session(
                session.id
            )
            items.append(
                {
                    "id": str(session.id),
                    "agent_id": str(session.agent_id),
                    "project_id": str(session.project_id),
                    "organization_id": str(session.organization_id),
                    "status": session.status,
                    "created_at": session.created_at.isoformat()
                    if session.created_at
                    else None,
                    "updated_at": session.updated_at.isoformat()
                    if session.updated_at
                    else None,
                    "alignment_history_count": alignment_history_count,
                }
            )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def add_alignment_history(
        self,
        session_id: UUID,
        user_instruction: str,
        alignment_result: dict,
        past_instructions_history: str | None = None,
        previous_extraction_output: str | None = None,
    ) -> dict[str, Any]:
        """
        Add alignment history record to a session.

        Automatically derives agent_id from session.

        Args:
            session_id: Session UUID
            user_instruction: User instruction for this alignment
            alignment_result: Alignment result data (key_terms, tool_invocation_rules)
            past_instructions_history: Past instructions history for context (optional)
            previous_extraction_output: Previous extraction output for iteration (optional)

        Returns:
            Created alignment history data

        Raises:
            HTTPException: If creation fails or session not found
        """
        try:
            # Get session to extract agent_id
            session = await self.session_repo.get_by_id(session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found",
                )

            # Create alignment history
            history = await self.history_repo.create(
                {
                    "session_id": session_id,
                    "agent_id": session.agent_id,
                    "user_instruction": user_instruction,
                    "past_instructions_history": past_instructions_history,
                    "previous_extraction_output": previous_extraction_output,
                    "alignment_result": alignment_result,
                }
            )

            await self.db.commit()

            return {
                "id": str(history.id),
                "session_id": str(history.session_id),
                "agent_id": str(history.agent_id),
                "user_instruction": history.user_instruction,
                "past_instructions_history": history.past_instructions_history,
                "previous_extraction_output": history.previous_extraction_output,
                "alignment_result": history.alignment_result,
                "created_at": history.created_at.isoformat()
                if history.created_at
                else None,
                "updated_at": history.updated_at.isoformat()
                if history.updated_at
                else None,
            }

        except HTTPException:
            await self.db.rollback()
            raise

        except IntegrityError as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Alignment history creation failed: {str(e)}",
            )

        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating alignment history: {str(e)}",
            )

    async def get_latest_alignment(self, session_id: UUID) -> dict[str, Any] | None:
        """
        Get the latest alignment result for a session.

        Args:
            session_id: Session UUID

        Returns:
            Latest alignment history data or None if no history exists

        Raises:
            HTTPException: If session not found
        """
        # Verify session exists
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        # Get latest alignment history
        history = await self.history_repo.get_latest_by_session(session_id)
        if not history:
            return None

        return {
            "id": str(history.id),
            "session_id": str(history.session_id),
            "agent_id": str(history.agent_id),
            "user_instruction": history.user_instruction,
            "past_instructions_history": history.past_instructions_history,
            "previous_extraction_output": history.previous_extraction_output,
            "alignment_result": history.alignment_result,
            "created_at": history.created_at.isoformat()
            if history.created_at
            else None,
            "updated_at": history.updated_at.isoformat()
            if history.updated_at
            else None,
        }

    async def complete_session(self, session_id: UUID) -> dict[str, Any]:
        """
        Mark session as completed.

        Args:
            session_id: Session UUID

        Returns:
            Updated session data

        Raises:
            HTTPException: If session not found or update fails
        """
        try:
            session = await self.session_repo.complete_session(session_id)
            if not session:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Session not found",
                )

            await self.db.commit()

            return await self.get_session(session.id)

        except HTTPException:
            await self.db.rollback()
            raise

        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error completing session: {str(e)}",
            )

    # ===== Dashboard Methods =====

    async def list_sessions_for_dashboard(
        self,
        agent_id: UUID,
        page: int = 1,
        page_size: int = 20,
        session_status: str | None = None,
    ) -> dict[str, Any]:
        """
        List sessions for dashboard display.

        Returns data formatted for frontend AlignmentSession type.

        Args:
            agent_id: Agent UUID
            page: Page number (1-indexed)
            page_size: Number of items per page
            session_status: Filter by status

        Returns:
            Dictionary with sessions list and total count
        """
        sessions, total = await self.session_repo.get_by_agent(
            agent_id=agent_id,
            page=page,
            page_size=page_size,
            status=session_status,
        )

        items = []
        for session in sessions:
            # Get latest alignment history for user_instruction and counts
            latest_alignment = await self.history_repo.get_latest_by_session(session.id)

            # Get validation logs count and check for invalid validations
            (
                validation_logs,
                validation_count,
            ) = await self.validation_log_repo.list_by_session(
                session.id, page=1, page_size=1000
            )

            # Calculate counts from alignment_result
            user_instruction = ""
            ambiguous_terms_count = 0
            resolved_terms_count = 0
            validation_rules_count = 0

            if latest_alignment:
                user_instruction = latest_alignment.user_instruction or ""
                alignment_result = latest_alignment.alignment_result or {}
                key_terms = alignment_result.get("key_terms", [])

                # Ambiguous = no user_provided_context, Resolved = has user_provided_context
                for term in key_terms:
                    if term.get("user_provided_context"):
                        resolved_terms_count += 1
                    else:
                        ambiguous_terms_count += 1

                validation_rules_count = len(
                    alignment_result.get("tool_invocation_rules", [])
                )

            # Check for invalid validations (should_proceed = False)
            has_invalid_validations = any(
                not (log.log_data or {})
                .get("validation_result", {})
                .get("should_proceed", True)
                for log in validation_logs
            )

            items.append(
                {
                    "session_id": str(session.id),
                    "user_instruction": user_instruction,
                    "ambiguous_terms_count": ambiguous_terms_count,
                    "resolved_terms_count": resolved_terms_count,
                    "validation_rules_count": validation_rules_count,
                    "validation_history_count": validation_count,
                    "has_invalid_validations": has_invalid_validations,
                    "created_at": session.created_at.isoformat()
                    if session.created_at
                    else "",
                    "updated_at": session.updated_at.isoformat()
                    if session.updated_at
                    else "",
                }
            )

        return {
            "sessions": items,
            "total": total,
        }

    async def get_session_detail_for_dashboard(
        self,
        session_id: UUID,
    ) -> dict[str, Any]:
        """
        Get session detail for dashboard display.

        Returns data formatted for frontend SessionData type.

        Args:
            session_id: Session UUID

        Returns:
            Dictionary with inference_result, validation_rules, validation_history,
            user_instruction_history

        Raises:
            HTTPException: If session not found
        """
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )

        # Get all alignment history for user_instruction_history
        all_alignments, _ = await self.history_repo.get_by_session(
            session_id, page=1, page_size=1000
        )

        # Build user_instruction_history (ordered by created_at ASC for chronological order)
        user_instruction_history: list[dict[str, str]] = []
        for alignment in reversed(all_alignments):  # reverse to get chronological order
            user_instruction_history.append(
                {
                    "user_instruction": alignment.user_instruction or "",
                    "created_at": alignment.created_at.isoformat()
                    if alignment.created_at
                    else "",
                }
            )

        # Get latest alignment history
        latest_alignment = await self.history_repo.get_latest_by_session(session_id)

        # Build inference_result
        inference_result: dict[str, Any] = {
            "user_instruction": "",
            "ambiguous_terms": [],
            "resolved_terms": [],
        }
        validation_rules: list[dict[str, Any]] = []
        disallowed_tools: list[str] = []

        if latest_alignment:
            inference_result["user_instruction"] = (
                latest_alignment.user_instruction or ""
            )
            alignment_result = latest_alignment.alignment_result or {}
            key_terms = alignment_result.get("key_terms", [])

            for term in key_terms:
                if term.get("user_provided_context"):
                    # Resolved term
                    inference_result["resolved_terms"].append(
                        {
                            "term": term.get("term", ""),
                            "category": term.get("category", ""),
                            "resolved_value": term.get("user_provided_context", ""),
                            "confidence": term.get("confidence", "LOW"),
                        }
                    )
                else:
                    # Ambiguous term
                    inference_result["ambiguous_terms"].append(
                        {
                            "term": term.get("term", ""),
                            "category": term.get("category", ""),
                        }
                    )

            # Get validation rules from alignment_result
            raw_rules = alignment_result.get("tool_invocation_rules", [])
            for rule in raw_rules:
                validation_rules.append(
                    {
                        "tool_name": rule.get("tool_name", ""),
                        "condition": rule.get("condition", ""),
                        "parameters": rule.get("parameters", {}),
                        "reasoning": rule.get("reasoning", ""),
                        "guardrail_definition": rule.get("guardrail_definition"),
                    }
                )

            # Get disallowed tools from alignment_result
            disallowed_tools = alignment_result.get("disallowed_tools", [])

        # Build validation_history from validation logs
        validation_logs, _ = await self.validation_log_repo.list_by_session(
            session_id, page=1, page_size=1000
        )

        validation_history: list[dict[str, Any]] = []
        for log in validation_logs:
            log_data = log.log_data or {}

            validation_history.append(
                {
                    "timestamp": log.created_at.isoformat() if log.created_at else "",
                    "timing": log_data.get("timing", ""),
                    "process_name": log_data.get("process_name", ""),
                    "process_type": log_data.get("process_type", ""),
                    "should_proceed": log_data.get("should_proceed", True),
                    "request_context": log_data.get("request_context", {}),
                    "evaluation_result": log_data.get("evaluation_result", {}),
                }
            )

        return {
            "inference_result": inference_result,
            "validation_rules": validation_rules,
            "validation_history": validation_history,
            "user_instruction_history": user_instruction_history,
            "disallowed_tools": disallowed_tools,
            "created_at": session.created_at.isoformat() if session.created_at else "",
            "updated_at": session.updated_at.isoformat() if session.updated_at else "",
        }


__all__ = ["SessionService"]
