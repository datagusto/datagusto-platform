"""
Organization service for managing organization operations.

This service handles organization-related operations including CRUD operations,
status management, and organization queries.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.organization_repository import OrganizationRepository


class OrganizationService:
    """Service for handling organization operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize the organization service.

        Args:
            db: Async database session
        """
        self.db = db
        self.org_repo = OrganizationRepository(db)

    async def get_organization(self, organization_id: UUID) -> Dict[str, Any]:
        """
        Get organization by ID with all related data.

        Args:
            organization_id: Organization UUID

        Returns:
            Dictionary containing organization data

        Raises:
            HTTPException: If organization not found
        """
        org = await self.org_repo.get_by_id_with_relations(organization_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        return {
            "id": str(org.id),
            "name": org.name,
            "is_active": await self.org_repo.is_active(org.id),
            "is_suspended": await self.org_repo.is_suspended(org.id),
            "is_archived": await self.org_repo.is_archived(org.id),
            "created_at": org.created_at.isoformat() if org.created_at else None,
            "updated_at": org.updated_at.isoformat() if org.updated_at else None,
        }

    async def create_organization(
        self, org_data: Dict[str, Any], created_by: UUID
    ) -> Dict[str, Any]:
        """
        Create a new organization.

        Args:
            org_data: Organization data (name, slug, description, etc.)
            created_by: UUID of user creating the organization

        Returns:
            Created organization data

        Raises:
            HTTPException: If creation fails
        """
        try:
            # Create organization
            org = await self.org_repo.create(org_data)

            # Activate organization by default
            await self.org_repo.activate(org.id)

            await self.db.commit()
            return await self.get_organization(org.id)

        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create organization: {str(e)}",
            )

    async def update_organization(
        self, organization_id: UUID, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update organization information.

        Args:
            organization_id: Organization UUID
            update_data: Data to update

        Returns:
            Updated organization data

        Raises:
            HTTPException: If organization not found or update fails
        """
        org = await self.org_repo.update_by_id(organization_id, update_data)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        await self.db.commit()
        return await self.get_organization(organization_id)

    async def suspend_organization(
        self,
        organization_id: UUID,
        reason: str,
        suspended_by: UUID,
        suspended_until: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Suspend an organization.

        Args:
            organization_id: Organization UUID to suspend
            reason: Reason for suspension
            suspended_by: UUID of user performing suspension
            suspended_until: Optional end date for suspension

        Returns:
            Updated organization data

        Raises:
            HTTPException: If organization not found
        """
        org = await self.org_repo.get_by_id(organization_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        await self.org_repo.suspend(
            organization_id, reason, suspended_by, suspended_until
        )
        await self.db.commit()
        return await self.get_organization(organization_id)

    async def lift_suspension(
        self, suspension_id: int, lifted_by: UUID
    ) -> Dict[str, Any]:
        """
        Lift organization suspension.

        Args:
            suspension_id: Suspension record ID
            lifted_by: UUID of user lifting the suspension

        Returns:
            Updated organization data

        Raises:
            HTTPException: If suspension not found
        """
        suspension = await self.org_repo.lift_suspension(suspension_id, lifted_by)
        if not suspension:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Suspension not found",
            )

        await self.db.commit()
        return await self.get_organization(suspension.organization_id)

    async def archive_organization(
        self, organization_id: UUID, reason: str, archived_by: UUID
    ) -> Dict[str, Any]:
        """
        Archive an organization (soft delete).

        Args:
            organization_id: Organization UUID to archive
            reason: Reason for archiving
            archived_by: UUID of user performing archiving

        Returns:
            Updated organization data

        Raises:
            HTTPException: If organization not found or already archived
        """
        org = await self.org_repo.get_by_id(organization_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        # Deactivate organization first
        await self.org_repo.deactivate(organization_id)

        # Archive organization
        await self.org_repo.archive(organization_id, reason, archived_by)
        await self.db.commit()
        return await self.get_organization(organization_id)

    async def unarchive_organization(self, organization_id: UUID) -> Dict[str, Any]:
        """
        Unarchive an organization (restore from soft delete).

        Args:
            organization_id: Organization UUID to unarchive

        Returns:
            Updated organization data

        Raises:
            HTTPException: If organization not found or not archived
        """
        if not await self.org_repo.is_archived(organization_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization is not archived",
            )

        # Unarchive organization
        await self.org_repo.unarchive(organization_id)

        # Reactivate organization
        await self.org_repo.activate(organization_id)

        await self.db.commit()
        return await self.get_organization(organization_id)

    async def list_active_organizations(
        self, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all active organizations.

        Args:
            limit: Maximum number of organizations to return
            offset: Number of organizations to skip

        Returns:
            List of organization dictionaries
        """
        orgs = await self.org_repo.list_active(limit, offset)

        result = []
        for org in orgs:
            org_data = await self.get_organization(org.id)
            result.append(org_data)

        return result

    async def delete_organization(self, organization_id: UUID) -> bool:
        """
        Permanently delete an organization.

        Args:
            organization_id: Organization UUID to delete

        Returns:
            True if deleted successfully

        Raises:
            HTTPException: If organization not found

        Warning:
            This is a hard delete and cannot be undone.
            Consider using archive_organization instead for soft delete.
        """
        success = await self.org_repo.delete(organization_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )

        await self.db.commit()
        return True
