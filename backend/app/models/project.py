"""
Project models for multi-tenant architecture.

This module contains all project-related SQLAlchemy models following
ultra-fine-grained table separation principles. Projects are the primary
workspace container that users create within their organizations to organize
work and resources.

Models:
    - Project: Core project entity (identity only)
    - ProjectOwner: Project ownership tracking (one owner per project)
    - ProjectMember: Many-to-many user-project membership
    - ProjectActiveStatus: Active project tracking (presence-based)
    - ProjectArchive: Soft delete pattern for projects
"""

from sqlalchemy import (
    Column,
    Text,
    ForeignKey,
    BigInteger,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel, uuid_column


class Project(BaseModel):
    """
    Core projects table for multi-tenant project management.

    Follows ultra-fine-grained separation - only essential project information.
    Projects are workspaces that users create within organizations.

    Attributes:
        id: Unique identifier for the project (UUID primary key)
        organization_id: Organization this project belongs to (required)
        name: Project display name (required)
        created_by: User who created the project (required, audit trail)
        created_at: Timestamp when project was created (auto-managed)
        updated_at: Timestamp when project was last updated (auto-managed)

    Relationships:
        organization: The organization this project belongs to
        creator: User who created the project
        owner: Project ownership record (ProjectOwner, one-to-one)
        members: Project membership records (ProjectMember)
        active_status: Active status record (ProjectActiveStatus, one-to-one)
        archive: Archive record if soft-deleted (ProjectArchive, one-to-one)

    Example:
        >>> # Create new project
        >>> project = Project(
        ...     organization_id=org_id,
        ...     name="Q4 Marketing Campaign",
        ...     created_by=user_id
        ... )
        >>> session.add(project)
        >>> await session.commit()
        >>>
        >>> # Query projects in organization
        >>> projects = await session.execute(
        ...     select(Project)
        ...     .where(Project.organization_id == org_id)
        ...     .order_by(Project.created_at.desc())
        ... )

    Note:
        - organization_id is required (multi-tenant isolation)
        - name is required (no anonymous projects)
        - created_by provides audit trail
        - RLS policies automatically filter by organization_id
    """

    __tablename__ = "projects"

    id = uuid_column(primary_key=True)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        comment="Organization this project belongs to",
    )
    name = Column(Text, nullable=False, comment="Project display name")
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="User who created the project",
    )

    # Relationships
    organization = relationship("Organization", backref="projects")
    creator = relationship(
        "User", foreign_keys=[created_by], backref="created_projects"
    )
    owner = relationship(
        "ProjectOwner",
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan",
    )
    members = relationship(
        "ProjectMember", back_populates="project", cascade="all, delete-orphan"
    )
    active_status = relationship(
        "ProjectActiveStatus",
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan",
    )
    archive = relationship(
        "ProjectArchive",
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("projects_organization_id_idx", "organization_id"),
        Index("projects_created_by_idx", "created_by"),
        Index("projects_name_idx", "name"),
        Index("projects_org_name_idx", "organization_id", "name"),
    )


class ProjectActiveStatus(BaseModel):
    """
    Active projects tracking using presence-based state management.

    Attributes:
        project_id: FK to projects (primary key)
        created_at: When the project was activated (inherited, semantically "activated_at")

    Relationships:
        project: The project this status belongs to

    Example:
        >>> # Activate project
        >>> status = ProjectActiveStatus(project_id=project_id)
        >>> session.add(status)
        >>> await session.commit()
        >>>
        >>> # Check if active
        >>> result = await session.execute(
        ...     select(ProjectActiveStatus)
        ...     .where(ProjectActiveStatus.project_id == project_id)
        ... )
        >>> is_active = result.scalar_one_or_none() is not None
        >>>
        >>> # Deactivate project
        >>> await session.delete(status)
        >>> await session.commit()

    Note:
        - No updated_at needed for status table (state is binary)
        - Activation timestamp is stored in created_at
        - To deactivate, simply delete the record
    """

    __tablename__ = "project_active_status"

    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        comment="Project ID (also primary key)",
    )

    # Override BaseModel to remove updated_at
    updated_at = None

    # Relationship
    project = relationship("Project", back_populates="active_status")


class ProjectArchive(BaseModel):
    """
    Project archives (soft delete pattern).

    Attributes:
        project_id: FK to projects (primary key)
        reason: Reason for archiving (required for audit)
        archived_by: FK to users (who performed the archiving)
        created_at: When project was archived (inherited, semantically "archived_at")
        updated_at: When archive record was last updated

    Relationships:
        project: The archived project
        archiver: User who performed the archiving

    Example:
        >>> # Archive project
        >>> archive = ProjectArchive(
        ...     project_id=project_id,
        ...     reason="Project completed",
        ...     archived_by=user_id
        ... )
        >>> session.add(archive)
        >>> await session.commit()
        >>>
        >>> # Check if archived
        >>> result = await session.execute(
        ...     select(ProjectArchive)
        ...     .where(ProjectArchive.project_id == project_id)
        ... )
        >>> is_archived = result.scalar_one_or_none() is not None
        >>>
        >>> # List non-archived projects
        >>> result = await session.execute(
        ...     select(Project)
        ...     .outerjoin(ProjectArchive)
        ...     .where(ProjectArchive.project_id.is_(None))
        ... )

    Note:
        - Soft delete: project record is not deleted from database
        - Presence of archive record indicates deleted state
        - Always include reason for compliance
        - created_at semantically represents "archived_at"
    """

    __tablename__ = "project_archives"

    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        comment="Archived project ID (also primary key)",
    )
    reason = Column(Text, nullable=False, comment="Reason for archiving (audit trail)")
    archived_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="User who performed the archiving",
    )

    # Relationships
    project = relationship("Project", back_populates="archive")
    archiver = relationship("User", foreign_keys=[archived_by])


class ProjectOwner(BaseModel):
    """
    Project owner (highest privilege level, one owner per project).

    Attributes:
        project_id: FK to projects (primary key, enforces one owner)
        user_id: FK to users (the owner)
        created_at: When ownership was established (inherited, semantically "transferred_at")
        updated_at: When ownership record was last updated

    Relationships:
        project: The project
        user: The owner user

    Example:
        >>> # Set project owner
        >>> owner = ProjectOwner(
        ...     project_id=project_id,
        ...     user_id=user_id
        ... )
        >>> session.add(owner)
        >>> await session.commit()
        >>>
        >>> # Get current owner
        >>> result = await session.execute(
        ...     select(User)
        ...     .join(ProjectOwner)
        ...     .where(ProjectOwner.project_id == project_id)
        ... )
        >>> owner_user = result.scalar_one_or_none()
        >>>
        >>> # Transfer ownership
        >>> owner.user_id = new_owner_user_id
        >>> await session.commit()

    Note:
        - project_id is PRIMARY KEY (enforces one owner per project)
        - Owner must also be member (validate at service layer)
        - created_at semantically represents initial ownership or last transfer
        - Ownership transfer updates user_id and updated_at
        - Owner cannot be removed without transferring first
    """

    __tablename__ = "project_owners"

    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        comment="Project ID (primary key enforces one owner)",
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Owner user ID",
    )

    # Relationships
    project = relationship("Project", back_populates="owner")
    user = relationship("User", foreign_keys=[user_id], backref="owned_projects")

    __table_args__ = (Index("project_owners_user_id_idx", "user_id"),)


class ProjectMember(BaseModel):
    """
    Project membership (many-to-many relationship between users and projects).

    Attributes:
        id: Unique membership record ID (auto-increment)
        project_id: FK to projects
        user_id: FK to users
        created_at: When user joined the project (inherited, semantically "joined_at")
        updated_at: When membership record was last updated

    Relationships:
        project: The project
        user: The member user

    Example:
        >>> # Add user to project
        >>> member = ProjectMember(
        ...     project_id=project_id,
        ...     user_id=user_id
        ... )
        >>> session.add(member)
        >>> await session.commit()
        >>>
        >>> # List project members
        >>> result = await session.execute(
        ...     select(User)
        ...     .join(ProjectMember)
        ...     .where(ProjectMember.project_id == project_id)
        ... )
        >>> members = result.scalars().all()
        >>>
        >>> # List user's projects
        >>> result = await session.execute(
        ...     select(Project)
        ...     .join(ProjectMember)
        ...     .where(ProjectMember.user_id == user_id)
        ... )
        >>> projects = result.scalars().all()

    Note:
        - Unique constraint on (project_id, user_id) prevents duplicates
        - created_at semantically represents "joined_at"
        - Deletion removes membership (user loses access)
        - CASCADE delete when project or user is deleted
    """

    __tablename__ = "project_members"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Unique membership record ID",
    )
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="Project ID",
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Member user ID",
    )

    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", foreign_keys=[user_id], backref="project_memberships")

    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="project_members_unique"),
        Index("project_members_project_id_idx", "project_id"),
        Index("project_members_user_id_idx", "user_id"),
    )


__all__ = [
    "Project",
    "ProjectActiveStatus",
    "ProjectArchive",
    "ProjectOwner",
    "ProjectMember",
]