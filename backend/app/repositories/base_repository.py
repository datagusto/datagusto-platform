from typing import Dict, Any, Optional, List, TypeVar, Generic, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase
from uuid import UUID

T = TypeVar("T", bound=DeclarativeBase)


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations for all entities."""

    def __init__(self, db: AsyncSession, model: Type[T]):
        """
        Initialize the repository with a database session and model.

        Args:
            db: Async database session
            model: SQLAlchemy model class
        """
        self.db = db
        self.model = model

    async def create(self, data: Dict[str, Any]) -> T:
        """
        Create a new entity in the database.

        Args:
            data: Entity data dictionary

        Returns:
            Created entity
        """
        entity = self.model(**data)
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """
        Get entity by ID.

        Args:
            entity_id: Entity UUID

        Returns:
            Entity or None if not found
        """
        stmt = select(self.model).where(self.model.id == entity_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        Get all entities with pagination.

        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip

        Returns:
            List of entities
        """
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update_by_id(
        self, entity_id: UUID, update_data: Dict[str, Any]
    ) -> Optional[T]:
        """
        Update entity by ID.

        Args:
            entity_id: Entity UUID
            update_data: Data to update

        Returns:
            Updated entity or None if not found
        """
        entity = await self.get_by_id(entity_id)
        if not entity:
            return None

        for key, value in update_data.items():
            setattr(entity, key, value)

        await self.db.flush()
        return entity

    async def delete_by_id(self, entity_id: UUID) -> bool:
        """
        Delete entity by ID.

        Args:
            entity_id: Entity UUID

        Returns:
            True if deleted, False if not found
        """
        entity = await self.get_by_id(entity_id)
        if not entity:
            return False

        await self.db.delete(entity)
        return True

    async def exists_by_id(self, entity_id: UUID) -> bool:
        """
        Check if entity exists by ID.

        Args:
            entity_id: Entity UUID

        Returns:
            True if exists, False otherwise
        """
        stmt = select(self.model.id).where(self.model.id == entity_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_by_id_and_organization(
        self, entity_id: UUID, organization_id: UUID
    ) -> Optional[T]:
        """
        Get entity by ID with organization filtering (multi-tenant support).

        Args:
            entity_id: Entity UUID
            organization_id: Organization UUID

        Returns:
            Entity or None if not found or not in organization

        Note:
            Only use this if the model has an organization_id column
        """
        stmt = select(self.model).where(
            self.model.id == entity_id, self.model.organization_id == organization_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_by_organization(
        self, organization_id: UUID, limit: int = 100, offset: int = 0
    ) -> List[T]:
        """
        Get all entities for a specific organization with pagination.

        Args:
            organization_id: Organization UUID
            limit: Maximum number of entities to return
            offset: Number of entities to skip

        Returns:
            List of entities

        Note:
            Only use this if the model has an organization_id column
        """
        stmt = (
            select(self.model)
            .where(self.model.organization_id == organization_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()
