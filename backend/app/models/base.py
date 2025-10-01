"""
Base model module for SQLAlchemy models.

This module provides the base model class and utility functions that all
database models inherit from. It includes automatic timestamp management
and UUID primary key generation helpers.
"""

import uuid
from sqlalchemy import Column, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class BaseModel(Base):
    """
    Abstract base model for all database tables.

    Provides automatic timestamp management with timezone-aware columns:
    - created_at: Automatically set on record creation
    - updated_at: Automatically updated on record modification

    All models inheriting from this class will have these timestamp fields
    unless explicitly overridden.

    Example:
        >>> class MyModel(BaseModel):
        ...     __tablename__ = "my_table"
        ...     id = Column(Integer, primary_key=True)
        ...     name = Column(String, nullable=False)
    """

    __abstract__ = True

    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp",
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Record last update timestamp",
    )


def uuid_column(primary_key: bool = False) -> Column:
    """
    Create a UUID column with proper defaults for PostgreSQL.

    This helper function creates a UUID column that automatically generates
    UUIDs using Python's uuid.uuid4() function. The column uses PostgreSQL's
    native UUID type for optimal storage and performance.

    Args:
        primary_key: If True, marks this column as the primary key.
                    Defaults to False.

    Returns:
        Column: A SQLAlchemy Column configured for UUID storage with
               automatic generation.

    Example:
        >>> class User(BaseModel):
        ...     __tablename__ = "users"
        ...     id = uuid_column(primary_key=True)
        ...     organization_id = uuid_column()

    Note:
        - UUIDs are stored as native PostgreSQL UUID type, not strings
        - as_uuid=True ensures Python UUID objects are returned, not strings
        - default=uuid.uuid4 generates UUIDs automatically on insert
    """
    return Column(
        UUID(as_uuid=True),
        primary_key=primary_key,
        default=uuid.uuid4,
        nullable=False if primary_key else True,
    )


__all__ = ["Base", "BaseModel", "uuid_column"]
