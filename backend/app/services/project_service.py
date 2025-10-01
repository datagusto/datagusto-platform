"""
Project service for managing project operations.

This service handles project-related operations including CRUD operations,
member management, owner management, and status management.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.repositories.project_repository import ProjectRepository
from app.repositories.project_owner_repository import ProjectOwnerRepository
from app.repositories.project_member_repository import ProjectMemberRepository
from app.services.permission_service import PermissionService


class ProjectService:
    """Service for handling project operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the project service.

        Args:
            db: Async database session
        """
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.owner_repo = ProjectOwnerRepository(db)
        self.member_repo = ProjectMemberRepository(db)
        self.permission_service = PermissionService(db)

    async def get_project(self, project_id: UUID) -> Dict[str, Any]:
        """
        Get project by ID with all related data.

        Args:
            project_id: Project UUID

        Returns:
            Dictionary containing project data

        Raises:
            HTTPException: If project not found
        """
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        return {
            "id": str(project.id),
            "organization_id": str(project.organization_id),
            "name": project.name,
            "created_by": str(project.created_by),
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            "is_active": await self.project_repo.is_active(project.id),
            "is_archived": await self.project_repo.is_archived(project.id),
        }

    async def list_projects(
        self,
        organization_id: UUID,
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None,
        is_archived: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        List projects in an organization with pagination and filtering.

        Args:
            organization_id: Organization UUID
            page: Page number (1-indexed)
            page_size: Number of items per page
            is_active: Filter by active status
            is_archived: Filter by archived status

        Returns:
            Dictionary with items, total, page, page_size
        """
        projects, total = await self.project_repo.get_by_organization(
            organization_id=organization_id,
            page=page,
            page_size=page_size,
            is_active=is_active,
            is_archived=is_archived,
        )

        items = []
        for project in projects:
            items.append({
                "id": str(project.id),
                "organization_id": str(project.organization_id),
                "name": project.name,
                "created_by": str(project.created_by),
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None,
                "is_active": await self.project_repo.is_active(project.id),
                "is_archived": await self.project_repo.is_archived(project.id),
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def create_project(
        self, organization_id: UUID, name: str, created_by: UUID
    ) -> Dict[str, Any]:
        """
        Create a new project.

        Automatically:
        - Activates the project
        - Sets creator as owner
        - Adds creator as member

        Args:
            organization_id: Organization UUID
            name: Project name
            created_by: UUID of user creating the project

        Returns:
            Created project data

        Raises:
            HTTPException: If creation fails
        """
        try:
            # Verify user is organization member
            is_member = await self.permission_service.is_member_or_above(
                organization_id=organization_id, user_id=created_by
            )
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User must be organization member to create project",
                )

            # Create project
            project_data = {
                "organization_id": organization_id,
                "name": name,
                "created_by": created_by,
            }
            project = await self.project_repo.create(project_data)

            # Activate project
            await self.project_repo.activate(project.id)

            # Set creator as owner
            await self.owner_repo.set_owner(project.id, created_by)

            # Add creator as member
            await self.member_repo.add_member(project.id, created_by)

            await self.db.commit()
            return await self.get_project(project.id)

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create project: {str(e)}",
            )

    async def update_project(
        self, project_id: UUID, name: str, user_id: UUID
    ) -> Dict[str, Any]:
        """
        Update project information.

        Args:
            project_id: Project UUID
            name: New project name
            user_id: User performing the update

        Returns:
            Updated project data

        Raises:
            HTTPException: If project not found or user lacks permission
        """
        # Verify project exists
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Verify user is owner or org admin
        is_owner = await self.owner_repo.is_owner(project_id, user_id)
        is_admin = await self.permission_service.is_admin_or_owner(
            user_id=user_id, organization_id=project.organization_id
        )

        if not (is_owner or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owner or organization admin can update project",
            )

        try:
            updated_project = await self.project_repo.update(project_id, {"name": name})
            if not updated_project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found",
                )

            await self.db.commit()
            return await self.get_project(project_id)

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update project: {str(e)}",
            )

    async def archive_project(
        self, project_id: UUID, user_id: UUID, reason: Optional[str] = None
    ) -> None:
        """
        Archive a project.

        Args:
            project_id: Project UUID
            user_id: User performing the archive
            reason: Optional reason for archiving

        Raises:
            HTTPException: If project not found or user lacks permission
        """
        # Verify project exists
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Verify user is owner or org admin
        is_owner = await self.owner_repo.is_owner(project_id, user_id)
        is_admin = await self.permission_service.is_admin_or_owner(
            user_id=user_id, organization_id=project.organization_id
        )

        if not (is_owner or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owner or organization admin can archive project",
            )

        try:
            await self.project_repo.archive(project_id, user_id, reason)
            await self.db.commit()

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to archive project: {str(e)}",
            )

    # Owner management

    async def get_owner(self, project_id: UUID) -> Dict[str, Any]:
        """
        Get project owner.

        Args:
            project_id: Project UUID

        Returns:
            Owner data

        Raises:
            HTTPException: If project or owner not found
        """
        owner = await self.owner_repo.get_by_project_id(project_id)
        if not owner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project owner not found",
            )

        return {
            "project_id": str(owner.project_id),
            "user_id": str(owner.user_id),
            "created_at": owner.created_at.isoformat() if owner.created_at else None,
            "updated_at": owner.updated_at.isoformat() if owner.updated_at else None,
        }

    async def transfer_ownership(
        self, project_id: UUID, new_owner_id: UUID, current_user_id: UUID
    ) -> Dict[str, Any]:
        """
        Transfer project ownership to another user.

        Automatically adds new owner as member if not already.

        Args:
            project_id: Project UUID
            new_owner_id: UUID of new owner
            current_user_id: UUID of user performing the transfer

        Returns:
            New owner data

        Raises:
            HTTPException: If project not found or user lacks permission
        """
        # Verify project exists
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Verify current user is owner or org admin
        is_owner = await self.owner_repo.is_owner(project_id, current_user_id)
        is_admin = await self.permission_service.is_admin_or_owner(
            user_id=current_user_id, organization_id=project.organization_id
        )

        if not (is_owner or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only current owner or organization admin can transfer ownership",
            )

        # Verify new owner is organization member
        is_org_member = await self.permission_service.is_member_or_above(
            organization_id=project.organization_id, user_id=new_owner_id
        )
        if not is_org_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New owner must be organization member",
            )

        try:
            # Add new owner as member if not already
            is_member = await self.member_repo.is_member(project_id, new_owner_id)
            if not is_member:
                await self.member_repo.add_member(project_id, new_owner_id)

            # Transfer ownership
            owner = await self.owner_repo.set_owner(project_id, new_owner_id)

            await self.db.commit()
            return {
                "project_id": str(owner.project_id),
                "user_id": str(owner.user_id),
                "created_at": owner.created_at.isoformat() if owner.created_at else None,
                "updated_at": owner.updated_at.isoformat() if owner.updated_at else None,
            }

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to transfer ownership: {str(e)}",
            )

    # Member management

    async def list_members(
        self, project_id: UUID, page: int = 1, page_size: int = 20
    ) -> Dict[str, Any]:
        """
        List project members with pagination.

        Args:
            project_id: Project UUID
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Dictionary with items, total, page, page_size
        """
        members, total = await self.member_repo.get_by_project_id(
            project_id, page, page_size
        )

        items = []
        for member in members:
            items.append({
                "id": member.id,
                "project_id": str(member.project_id),
                "user_id": str(member.user_id),
                "created_at": member.created_at.isoformat() if member.created_at else None,
                "updated_at": member.updated_at.isoformat() if member.updated_at else None,
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def add_member(
        self, project_id: UUID, user_id: UUID, current_user_id: UUID
    ) -> Dict[str, Any]:
        """
        Add a member to the project.

        Args:
            project_id: Project UUID
            user_id: User UUID to add
            current_user_id: UUID of user performing the action

        Returns:
            Created member data

        Raises:
            HTTPException: If project not found, user not org member, or lacks permission
        """
        # Verify project exists
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Verify current user is owner or org admin
        is_owner = await self.owner_repo.is_owner(project_id, current_user_id)
        is_admin = await self.permission_service.is_admin_or_owner(
            user_id=current_user_id, organization_id=project.organization_id
        )

        if not (is_owner or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owner or organization admin can add members",
            )

        # Verify user to add is organization member
        is_org_member = await self.permission_service.is_member_or_above(
            organization_id=project.organization_id, user_id=user_id
        )
        if not is_org_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User must be organization member to be added to project",
            )

        try:
            member = await self.member_repo.add_member(project_id, user_id)
            await self.db.commit()

            return {
                "id": member.id,
                "project_id": str(member.project_id),
                "user_id": str(member.user_id),
                "created_at": member.created_at.isoformat() if member.created_at else None,
                "updated_at": member.updated_at.isoformat() if member.updated_at else None,
            }

        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a project member",
            )
        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to add member: {str(e)}",
            )

    async def remove_member(
        self, project_id: UUID, user_id: UUID, current_user_id: UUID
    ) -> None:
        """
        Remove a member from the project.

        Cannot remove the project owner.

        Args:
            project_id: Project UUID
            user_id: User UUID to remove
            current_user_id: UUID of user performing the action

        Raises:
            HTTPException: If project not found, user is owner, or lacks permission
        """
        # Verify project exists
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        # Verify current user is owner or org admin
        is_owner = await self.owner_repo.is_owner(project_id, current_user_id)
        is_admin = await self.permission_service.is_admin_or_owner(
            user_id=current_user_id, organization_id=project.organization_id
        )

        if not (is_owner or is_admin):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owner or organization admin can remove members",
            )

        # Prevent removing owner
        is_target_owner = await self.owner_repo.is_owner(project_id, user_id)
        if is_target_owner:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove project owner. Transfer ownership first.",
            )

        try:
            removed = await self.member_repo.remove_member(project_id, user_id)
            if not removed:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User is not a project member",
                )

            await self.db.commit()

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to remove member: {str(e)}",
            )