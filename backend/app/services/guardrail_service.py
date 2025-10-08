"""
Guardrail service for managing guardrail operations.

This service handles guardrail-related operations including CRUD operations,
assignment management, and definition validation.
"""

from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.agent_repository import AgentRepository
from app.repositories.guardrail_assignment_repository import (
    GuardrailAssignmentRepository,
)
from app.repositories.guardrail_repository import GuardrailRepository
from app.repositories.project_member_repository import ProjectMemberRepository
from app.repositories.project_repository import ProjectRepository


class GuardrailService:
    """Service for handling guardrail operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the guardrail service.

        Args:
            db: Async database session
        """
        self.db = db
        self.guardrail_repo = GuardrailRepository(db)
        self.assignment_repo = GuardrailAssignmentRepository(db)
        self.project_repo = ProjectRepository(db)
        self.member_repo = ProjectMemberRepository(db)
        self.agent_repo = AgentRepository(db)

    async def get_guardrail(self, guardrail_id: UUID) -> dict[str, Any]:
        """
        Get guardrail by ID.

        Args:
            guardrail_id: Guardrail UUID

        Returns:
            Dictionary containing guardrail data

        Raises:
            HTTPException: If guardrail not found
        """
        guardrail = await self.guardrail_repo.get_by_id(guardrail_id)
        if not guardrail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guardrail not found",
            )

        # Get assigned agent count
        assigned_count = await self.assignment_repo.count_assigned_agents(guardrail.id)

        return {
            "id": str(guardrail.id),
            "project_id": str(guardrail.project_id),
            "organization_id": str(guardrail.organization_id),
            "name": guardrail.name,
            "definition": guardrail.definition,
            "created_by": str(guardrail.created_by),
            "created_at": guardrail.created_at.isoformat()
            if guardrail.created_at
            else None,
            "updated_at": guardrail.updated_at.isoformat()
            if guardrail.updated_at
            else None,
            "is_active": await self.guardrail_repo.is_active(guardrail.id),
            "is_archived": await self.guardrail_repo.is_archived(guardrail.id),
            "assigned_agent_count": assigned_count,
        }

    async def list_guardrails(
        self,
        project_id: UUID,
        page: int = 1,
        page_size: int = 20,
        is_active: bool | None = None,
        is_archived: bool | None = None,
    ) -> dict[str, Any]:
        """
        List guardrails in a project with pagination and filtering.

        Args:
            project_id: Project UUID
            page: Page number (1-indexed)
            page_size: Number of items per page
            is_active: Filter by active status
            is_archived: Filter by archived status

        Returns:
            Dictionary with items, total, page, page_size
        """
        guardrails, total = await self.guardrail_repo.get_by_project(
            project_id=project_id,
            page=page,
            page_size=page_size,
            is_active=is_active,
            is_archived=is_archived,
        )

        items = []
        for guardrail in guardrails:
            assigned_count = await self.assignment_repo.count_assigned_agents(
                guardrail.id
            )
            items.append(
                {
                    "id": str(guardrail.id),
                    "project_id": str(guardrail.project_id),
                    "organization_id": str(guardrail.organization_id),
                    "name": guardrail.name,
                    "definition": guardrail.definition,
                    "created_by": str(guardrail.created_by),
                    "created_at": guardrail.created_at.isoformat()
                    if guardrail.created_at
                    else None,
                    "updated_at": guardrail.updated_at.isoformat()
                    if guardrail.updated_at
                    else None,
                    "is_active": await self.guardrail_repo.is_active(guardrail.id),
                    "is_archived": await self.guardrail_repo.is_archived(guardrail.id),
                    "assigned_agent_count": assigned_count,
                }
            )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def create_guardrail(
        self, project_id: UUID, name: str, definition: dict[str, Any], created_by: UUID
    ) -> dict[str, Any]:
        """
        Create a new guardrail.

        Automatically activates the guardrail and sets organization_id from project.

        Args:
            project_id: Project UUID
            name: Guardrail name
            definition: JSONB definition
            created_by: UUID of user creating the guardrail

        Returns:
            Created guardrail data

        Raises:
            HTTPException: If creation fails or project not found
        """
        try:
            # Verify project exists and get organization_id
            project = await self.project_repo.get_by_id(project_id)
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found",
                )

            # Verify user is project member
            is_member = await self.member_repo.is_member(project_id, created_by)
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User must be project member to create guardrail",
                )

            # Create guardrail
            guardrail_data = {
                "project_id": project_id,
                "organization_id": project.organization_id,
                "name": name,
                "definition": definition,
                "created_by": created_by,
            }
            guardrail = await self.guardrail_repo.create(guardrail_data)

            # Activate guardrail
            await self.guardrail_repo.activate(guardrail.id)

            await self.db.commit()
            return await self.get_guardrail(guardrail.id)

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create guardrail: {str(e)}",
            )

    async def update_guardrail(
        self,
        guardrail_id: UUID,
        name: str | None,
        definition: dict[str, Any] | None,
        user_id: UUID,
    ) -> dict[str, Any]:
        """
        Update guardrail information.

        Args:
            guardrail_id: Guardrail UUID
            name: New guardrail name (optional)
            definition: New definition (optional)
            user_id: User performing the update

        Returns:
            Updated guardrail data

        Raises:
            HTTPException: If guardrail not found or user lacks permission
        """
        # Verify guardrail exists
        guardrail = await self.guardrail_repo.get_by_id(guardrail_id)
        if not guardrail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guardrail not found",
            )

        # Verify user is project member
        is_member = await self.member_repo.is_member(guardrail.project_id, user_id)
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User must be project member to update guardrail",
            )

        try:
            update_data = {}
            if name is not None:
                update_data["name"] = name
            if definition is not None:
                update_data["definition"] = definition

            updated_guardrail = await self.guardrail_repo.update(
                guardrail_id, update_data
            )
            if not updated_guardrail:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Guardrail not found",
                )

            await self.db.commit()
            return await self.get_guardrail(guardrail_id)

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update guardrail: {str(e)}",
            )

    async def archive_guardrail(
        self, guardrail_id: UUID, user_id: UUID, reason: str | None = None
    ) -> None:
        """
        Archive a guardrail.

        Args:
            guardrail_id: Guardrail UUID
            user_id: User performing the archive
            reason: Optional reason for archiving

        Raises:
            HTTPException: If guardrail not found or user lacks permission
        """
        # Verify guardrail exists
        guardrail = await self.guardrail_repo.get_by_id(guardrail_id)
        if not guardrail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guardrail not found",
            )

        # Verify user is project member
        is_member = await self.member_repo.is_member(guardrail.project_id, user_id)
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User must be project member to archive guardrail",
            )

        try:
            await self.guardrail_repo.archive(guardrail_id, user_id, reason)
            await self.db.commit()

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to archive guardrail: {str(e)}",
            )

    # Assignment management

    async def list_assignments(
        self, guardrail_id: UUID, page: int = 1, page_size: int = 20
    ) -> dict[str, Any]:
        """
        List agents assigned to a guardrail.

        Args:
            guardrail_id: Guardrail UUID
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Dictionary with items, total, page, page_size
        """
        assignments, total = await self.assignment_repo.get_by_guardrail_id(
            guardrail_id, page, page_size
        )

        items = []
        for assignment in assignments:
            items.append(
                {
                    "id": str(assignment.id),
                    "project_id": str(assignment.project_id),
                    "guardrail_id": str(assignment.guardrail_id),
                    "agent_id": str(assignment.agent_id),
                    "assigned_by": str(assignment.assigned_by),
                    "created_at": assignment.created_at.isoformat()
                    if assignment.created_at
                    else None,
                    "updated_at": assignment.updated_at.isoformat()
                    if assignment.updated_at
                    else None,
                }
            )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def assign_to_agent(
        self, guardrail_id: UUID, agent_id: UUID, user_id: UUID
    ) -> dict[str, Any]:
        """
        Assign guardrail to an agent.

        Args:
            guardrail_id: Guardrail UUID
            agent_id: Agent UUID
            user_id: User performing the assignment

        Returns:
            Created assignment data

        Raises:
            HTTPException: If guardrail/agent not found, not same project, or already assigned
        """
        # Verify guardrail exists
        guardrail = await self.guardrail_repo.get_by_id(guardrail_id)
        if not guardrail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guardrail not found",
            )

        # Verify agent exists
        agent = await self.agent_repo.get_by_id(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )

        # Verify same project
        if guardrail.project_id != agent.project_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Guardrail and agent must be in the same project",
            )

        # Verify user is project member
        is_member = await self.member_repo.is_member(guardrail.project_id, user_id)
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User must be project member to assign guardrail",
            )

        try:
            assignment = await self.assignment_repo.assign(
                guardrail_id=guardrail_id,
                agent_id=agent_id,
                project_id=guardrail.project_id,
                assigned_by=user_id,
            )
            await self.db.commit()

            return {
                "id": str(assignment.id),
                "project_id": str(assignment.project_id),
                "guardrail_id": str(assignment.guardrail_id),
                "agent_id": str(assignment.agent_id),
                "assigned_by": str(assignment.assigned_by),
                "created_at": assignment.created_at.isoformat()
                if assignment.created_at
                else None,
                "updated_at": assignment.updated_at.isoformat()
                if assignment.updated_at
                else None,
            }

        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Guardrail is already assigned to this agent",
            )
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to assign guardrail: {str(e)}",
            )

    async def unassign_from_agent(
        self, guardrail_id: UUID, agent_id: UUID, user_id: UUID
    ) -> None:
        """
        Unassign guardrail from an agent.

        Args:
            guardrail_id: Guardrail UUID
            agent_id: Agent UUID
            user_id: User performing the unassignment

        Raises:
            HTTPException: If assignment not found or user lacks permission
        """
        # Verify guardrail exists
        guardrail = await self.guardrail_repo.get_by_id(guardrail_id)
        if not guardrail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guardrail not found",
            )

        # Verify user is project member
        is_member = await self.member_repo.is_member(guardrail.project_id, user_id)
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User must be project member to unassign guardrail",
            )

        try:
            unassigned = await self.assignment_repo.unassign(guardrail_id, agent_id)
            if not unassigned:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assignment not found",
                )

            await self.db.commit()

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to unassign guardrail: {str(e)}",
            )

    async def list_agent_guardrails(
        self, agent_id: UUID, page: int = 1, page_size: int = 20
    ) -> dict[str, Any]:
        """
        List guardrails assigned to an agent.

        Args:
            agent_id: Agent UUID
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Dictionary with guardrail items
        """
        assignments, total = await self.assignment_repo.get_by_agent_id(
            agent_id, page, page_size
        )

        items = []
        for assignment in assignments:
            guardrail = await self.guardrail_repo.get_by_id(assignment.guardrail_id)
            if guardrail:
                assigned_count = await self.assignment_repo.count_assigned_agents(
                    guardrail.id
                )
                items.append(
                    {
                        "id": str(guardrail.id),
                        "project_id": str(guardrail.project_id),
                        "organization_id": str(guardrail.organization_id),
                        "name": guardrail.name,
                        "definition": guardrail.definition,
                        "created_by": str(guardrail.created_by),
                        "created_at": guardrail.created_at.isoformat()
                        if guardrail.created_at
                        else None,
                        "updated_at": guardrail.updated_at.isoformat()
                        if guardrail.updated_at
                        else None,
                        "is_active": await self.guardrail_repo.is_active(guardrail.id),
                        "is_archived": await self.guardrail_repo.is_archived(
                            guardrail.id
                        ),
                        "assigned_agent_count": assigned_count,
                    }
                )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
