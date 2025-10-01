"""
Organization models for multi-tenant architecture.

This module contains all organization-related SQLAlchemy models following
ultra-fine-grained table separation principles. Each table has a single,
clear responsibility and state management is handled through separate tables.

Models:
    - Organization: Core organization entity (identity only)
    - OrganizationActiveStatus: Active organization tracking (presence-based)
    - OrganizationSuspension: Suspension history with audit trail
    - OrganizationArchive: Soft delete pattern for organizations
    - OrganizationMember: Many-to-many user-organization membership
    - OrganizationAdmin: Admin privilege tracking
    - OrganizationOwner: Ownership tracking (one owner per organization)
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


class Organization(BaseModel):
    """
    Core organization table for multi-tenant architecture.

    This table stores only essential organization identity information.
    Following ultra-fine-grained separation principles, all optional data,
    state management, and relationships are stored in separate tables.

    Attributes:
        id: Unique identifier for the organization (UUID primary key)
        name: Organization display name (required)
        created_at: Timestamp when organization was created (auto-managed)
        updated_at: Timestamp when organization was last updated (auto-managed)

    Relationships:
        members: Membership records (OrganizationMember, N:M with User)
        admins: Admin privilege records (OrganizationAdmin)
        owner: Ownership record (OrganizationOwner, one-to-one)
        active_status: Active status record (OrganizationActiveStatus, one-to-one)
        suspensions: Suspension history records (OrganizationSuspension)
        archive: Archive record if soft-deleted (OrganizationArchive, one-to-one)

    Example:
        >>> # Create new organization
        >>> org = Organization(name="Acme Corporation")
        >>> session.add(org)
        >>> await session.commit()
        >>>
        >>> # Query with relationships
        >>> org = await session.execute(
        ...     select(Organization)
        ...     .options(joinedload(Organization.members))
        ...     .where(Organization.id == org_id)
        ... )

    Note:
        - Name is required but not unique (multiple orgs can have same name)
        - Organization state is managed through separate tables
        - Always use cascade="all, delete-orphan" for child relationships
    """

    __tablename__ = "organizations"

    id = uuid_column(primary_key=True)
    name = Column(Text, nullable=False, comment="Organization display name")

    # Relationships to other tables
    # Note: User-Organization relationship is N:M via organization_members table
    members = relationship(
        "OrganizationMember",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    admins = relationship(
        "OrganizationAdmin", back_populates="organization", cascade="all, delete-orphan"
    )
    owner = relationship(
        "OrganizationOwner",
        back_populates="organization",
        uselist=False,
        cascade="all, delete-orphan",
    )
    active_status = relationship(
        "OrganizationActiveStatus",
        back_populates="organization",
        uselist=False,
        cascade="all, delete-orphan",
    )
    suspensions = relationship(
        "OrganizationSuspension",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    archive = relationship(
        "OrganizationArchive",
        back_populates="organization",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (Index("organizations_name_idx", "name"),)


class OrganizationActiveStatus(BaseModel):
    """
    Active organizations tracking using presence-based state management.

    This table uses the "presence = state" pattern. If a record exists for
    an organization, that organization is active. No record means inactive.
    This approach avoids nullable columns and boolean flags.

    Attributes:
        organization_id: FK to organizations (primary key)
        created_at: When the organization was activated (inherited, renamed to activated_at semantically)

    Relationships:
        organization: The organization this status belongs to

    Example:
        >>> # Activate organization
        >>> status = OrganizationActiveStatus(organization_id=org_id)
        >>> session.add(status)
        >>> await session.commit()
        >>>
        >>> # Check if active
        >>> is_active = await session.execute(
        ...     select(OrganizationActiveStatus)
        ...     .where(OrganizationActiveStatus.organization_id == org_id)
        ... )
        >>> active = is_active.scalar_one_or_none() is not None
        >>>
        >>> # Deactivate organization
        >>> await session.delete(status)
        >>> await session.commit()

    Note:
        - No updated_at needed for status table (state is binary: exists or not)
        - Activation timestamp is stored in created_at
        - To deactivate, simply delete the record
    """

    __tablename__ = "organization_active_status"

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        comment="Organization ID (also primary key)",
    )

    # Override BaseModel to remove updated_at (not needed for status table)
    # Keep created_at but semantically represents "activated_at"
    updated_at = None

    # Relationship
    organization = relationship("Organization", back_populates="active_status")


class OrganizationSuspension(BaseModel):
    """
    Organization suspension history with full audit trail.

    This table tracks all suspensions for organizations, including who suspended
    them, when, and why. Multiple suspension records per organization are allowed,
    creating a complete audit history. Current suspensions have lifted_at = NULL.

    Attributes:
        id: Unique suspension record ID (auto-increment)
        organization_id: FK to organizations
        reason: Reason for suspension (required for audit)
        suspended_by: FK to users (who performed the suspension)
        created_at: When suspension was created (inherited, semantically "suspended_at")
        updated_at: When suspension record was last updated

    Relationships:
        organization: The suspended organization
        suspender: User who performed the suspension

    Example:
        >>> # Suspend organization
        >>> suspension = OrganizationSuspension(
        ...     organization_id=org_id,
        ...     reason="Payment failure",
        ...     suspended_by=admin_user_id
        ... )
        >>> session.add(suspension)
        >>> await session.commit()
        >>>
        >>> # Get active suspension
        >>> result = await session.execute(
        ...     select(OrganizationSuspension)
        ...     .where(OrganizationSuspension.organization_id == org_id)
        ...     .order_by(OrganizationSuspension.created_at.desc())
        ...     .limit(1)
        ... )
        >>> current_suspension = result.scalar_one_or_none()

    Note:
        - Multiple suspensions allowed (history preserved)
        - Always include reason for compliance and audit
        - Latest suspension indicates current status
        - created_at semantically represents "suspended_at"
    """

    __tablename__ = "organization_suspensions"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Unique suspension record ID",
    )
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        comment="Suspended organization ID",
    )
    reason = Column(Text, nullable=False, comment="Reason for suspension (audit trail)")
    suspended_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="User who performed the suspension",
    )

    # Relationships
    organization = relationship("Organization", back_populates="suspensions")
    suspender = relationship("User", foreign_keys=[suspended_by])

    __table_args__ = (Index("organization_suspensions_org_id_idx", "organization_id"),)


class OrganizationArchive(BaseModel):
    """
    Organization archives (soft delete pattern).

    This table implements soft deletion for organizations. Instead of permanently
    deleting organizations, we create an archive record that preserves the
    deletion context and audit trail. The actual organization record remains
    in the database for referential integrity and historical queries.

    Attributes:
        organization_id: FK to organizations (primary key)
        reason: Reason for archiving (required for audit)
        archived_by: FK to users (who performed the archiving)
        created_at: When organization was archived (inherited, semantically "archived_at")
        updated_at: When archive record was last updated

    Relationships:
        organization: The archived organization
        archiver: User who performed the archiving

    Example:
        >>> # Archive organization
        >>> archive = OrganizationArchive(
        ...     organization_id=org_id,
        ...     reason="Organization closed",
        ...     archived_by=admin_user_id
        ... )
        >>> session.add(archive)
        >>> await session.commit()
        >>>
        >>> # Check if archived
        >>> is_archived = await session.execute(
        ...     select(OrganizationArchive)
        ...     .where(OrganizationArchive.organization_id == org_id)
        ... )
        >>> archived = is_archived.scalar_one_or_none() is not None
        >>>
        >>> # List non-archived organizations
        >>> orgs = await session.execute(
        ...     select(Organization)
        ...     .outerjoin(OrganizationArchive)
        ...     .where(OrganizationArchive.organization_id.is_(None))
        ... )

    Note:
        - Soft delete: organization record is not deleted from database
        - Presence of archive record indicates deleted state
        - Always include reason for compliance
        - created_at semantically represents "archived_at"
    """

    __tablename__ = "organization_archives"

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        comment="Archived organization ID (also primary key)",
    )
    reason = Column(Text, nullable=False, comment="Reason for archiving (audit trail)")
    archived_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="User who performed the archiving",
    )

    # Relationships
    organization = relationship("Organization", back_populates="archive")
    archiver = relationship("User", foreign_keys=[archived_by])


class OrganizationMember(BaseModel):
    """
    Organization membership (many-to-many relationship between users and organizations).

    This table tracks which users belong to which organizations. A user can be
    a member of multiple organizations, and an organization can have multiple
    members. This is the foundation of multi-tenant access control.

    Attributes:
        id: Unique membership record ID (auto-increment)
        organization_id: FK to organizations
        user_id: FK to users
        created_at: When user joined the organization (inherited, semantically "joined_at")
        updated_at: When membership record was last updated

    Relationships:
        organization: The organization
        user: The member user

    Example:
        >>> # Add user to organization
        >>> membership = OrganizationMember(
        ...     organization_id=org_id,
        ...     user_id=user_id
        ... )
        >>> session.add(membership)
        >>> await session.commit()
        >>>
        >>> # List organization members
        >>> result = await session.execute(
        ...     select(User)
        ...     .join(OrganizationMember)
        ...     .where(OrganizationMember.organization_id == org_id)
        ... )
        >>> members = result.scalars().all()
        >>>
        >>> # List user's organizations
        >>> result = await session.execute(
        ...     select(Organization)
        ...     .join(OrganizationMember)
        ...     .where(OrganizationMember.user_id == user_id)
        ... )
        >>> orgs = result.scalars().all()

    Note:
        - Unique constraint on (organization_id, user_id) prevents duplicates
        - created_at semantically represents "joined_at"
        - Deletion removes membership (user loses access)
        - CASCADE delete when organization or user is deleted
    """

    __tablename__ = "organization_members"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Unique membership record ID",
    )
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        comment="Organization ID",
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Member user ID",
    )

    # Relationships
    organization = relationship("Organization", back_populates="members")
    user = relationship(
        "User", foreign_keys=[user_id], backref="organization_memberships"
    )

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "user_id", name="organization_members_unique"
        ),
        Index("organization_members_org_id_idx", "organization_id"),
        Index("organization_members_user_id_idx", "user_id"),
    )


class OrganizationAdmin(BaseModel):
    """
    Organization administrators (subset of members with admin privileges).

    This table tracks which members have admin privileges in an organization.
    Admins can manage members, modify organization settings, but cannot transfer
    ownership. An admin must also be a member (enforced at application layer).

    Attributes:
        id: Unique admin record ID (auto-increment)
        organization_id: FK to organizations
        user_id: FK to users
        granted_by: FK to users (who granted admin privilege)
        created_at: When admin privilege was granted (inherited, semantically "granted_at")
        updated_at: When admin record was last updated

    Relationships:
        organization: The organization
        user: The admin user
        granter: User who granted the admin privilege

    Example:
        >>> # Grant admin privilege
        >>> admin = OrganizationAdmin(
        ...     organization_id=org_id,
        ...     user_id=user_id,
        ...     granted_by=owner_user_id
        ... )
        >>> session.add(admin)
        >>> await session.commit()
        >>>
        >>> # Check if user is admin
        >>> result = await session.execute(
        ...     select(OrganizationAdmin)
        ...     .where(
        ...         OrganizationAdmin.organization_id == org_id,
        ...         OrganizationAdmin.user_id == user_id
        ...     )
        ... )
        >>> is_admin = result.scalar_one_or_none() is not None
        >>>
        >>> # Revoke admin privilege
        >>> await session.delete(admin)
        >>> await session.commit()

    Note:
        - Unique constraint on (organization_id, user_id) prevents duplicates
        - User must be member before becoming admin (validate at service layer)
        - granted_by creates audit trail
        - created_at semantically represents "granted_at"
        - Deletion revokes admin privilege (user remains member)
    """

    __tablename__ = "organization_admins"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Unique admin record ID",
    )
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        comment="Organization ID",
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Admin user ID",
    )
    granted_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="User who granted admin privilege",
    )

    # Relationships
    organization = relationship("Organization", back_populates="admins")
    user = relationship("User", foreign_keys=[user_id], backref="admin_organizations")
    granter = relationship("User", foreign_keys=[granted_by])

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "user_id", name="organization_admins_unique"
        ),
        Index("organization_admins_org_id_idx", "organization_id"),
    )


class OrganizationOwner(BaseModel):
    """
    Organization owner (highest privilege level, one owner per organization).

    This table tracks organization ownership. Each organization has exactly one
    owner who has full control including the ability to transfer ownership,
    delete the organization, and manage all resources.

    Attributes:
        organization_id: FK to organizations (primary key, enforces one owner)
        user_id: FK to users (the owner)
        created_at: When ownership was established (inherited, semantically "transferred_at")
        updated_at: When ownership record was last updated

    Relationships:
        organization: The organization
        user: The owner user

    Example:
        >>> # Set organization owner
        >>> owner = OrganizationOwner(
        ...     organization_id=org_id,
        ...     user_id=user_id
        ... )
        >>> session.add(owner)
        >>> await session.commit()
        >>>
        >>> # Get current owner
        >>> result = await session.execute(
        ...     select(User)
        ...     .join(OrganizationOwner)
        ...     .where(OrganizationOwner.organization_id == org_id)
        ... )
        >>> owner_user = result.scalar_one_or_none()
        >>>
        >>> # Transfer ownership
        >>> owner.user_id = new_owner_user_id
        >>> await session.commit()

    Note:
        - organization_id is PRIMARY KEY (enforces one owner per org)
        - Owner must also be member and admin (validate at service layer)
        - created_at semantically represents initial ownership or last transfer
        - Ownership transfer updates user_id and updated_at
        - Owner cannot be removed without transferring first
    """

    __tablename__ = "organization_owners"

    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        comment="Organization ID (primary key enforces one owner)",
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Owner user ID",
    )

    # Relationships
    organization = relationship("Organization", back_populates="owner")
    user = relationship("User", foreign_keys=[user_id], backref="owned_organizations")

    __table_args__ = (Index("organization_owners_user_id_idx", "user_id"),)


__all__ = [
    "Organization",
    "OrganizationActiveStatus",
    "OrganizationSuspension",
    "OrganizationArchive",
    "OrganizationMember",
    "OrganizationAdmin",
    "OrganizationOwner",
]
