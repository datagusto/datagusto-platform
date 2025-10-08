"""
User models for multi-tenant architecture.

This module contains all user-related SQLAlchemy models following
ultra-fine-grained table separation principles. The User model stores
only essential identity information, with profile, authentication, and
state data separated into dedicated tables.

Models:
    - User: Core user entity (identity only)
    - UserProfile: Optional profile information (name, bio, etc.)
    - UserLoginPassword: Password-based authentication credentials
    - UserActiveStatus: Active user tracking (presence-based)
    - UserSuspension: Suspension history with audit trail
    - UserArchive: Soft delete pattern for users
"""

from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, uuid_column


class User(BaseModel):
    """
    Core user table for multi-tenant architecture.

    This table stores only essential user identity information and organizational
    relationship. Following ultra-fine-grained separation principles, all profile
    data, authentication credentials, and state management are stored in separate
    tables.

    Attributes:
        id: Unique identifier for the user (UUID primary key)
        created_at: Timestamp when user was created (auto-managed)
        updated_at: Timestamp when user was last updated (auto-managed)

    Relationships:
        profile: Optional profile information (UserProfile, one-to-one)
        login_password: Password authentication credentials (UserLoginPassword, one-to-one)
        active_status: Active status record (UserActiveStatus, one-to-one)
        suspensions: Suspension history records (UserSuspension)
        archive: Archive record if soft-deleted (UserArchive, one-to-one)

    Note:
        - User-Organization relationship is N:M via organization_members table
        - No direct organization_id field (use OrganizationMember for organization access)

    Example:
        >>> # Create new user
        >>> user = User()
        >>> session.add(user)
        >>> await session.commit()
        >>>
        >>> # Add user to organization via OrganizationMember
        >>> member = OrganizationMember(organization_id=org_id, user_id=user.id)
        >>> session.add(member)
        >>> await session.commit()
        >>>
        >>> # Query with relationships
        >>> user = await session.execute(
        ...     select(User)
        ...     .options(
        ...         joinedload(User.profile),
        ...         joinedload(User.login_password)
        ...     )
        ...     .where(User.id == user_id)
        ... )
    """

    __tablename__ = "users"

    id = uuid_column(primary_key=True)

    # Relationships to other tables
    # Note: User-Organization relationship is N:M via organization_members table
    profile = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    login_password = relationship(
        "UserLoginPassword",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    active_status = relationship(
        "UserActiveStatus",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    archive = relationship(
        "UserArchive",
        back_populates="user",
        foreign_keys="UserArchive.user_id",
        uselist=False,
        cascade="all, delete-orphan",
    )


class UserProfile(BaseModel):
    """
    User profile information (optional).

    This table stores optional user profile data. Following the principle of
    "no NULLs", if a user has no profile, no record exists. All profile fields
    can be added to this table as the application evolves.

    Attributes:
        user_id: FK to users (primary key)
        name: Display name (required if profile exists)
        bio: User biography (optional)
        avatar_url: URL to user avatar image (optional)
        timezone: User timezone preference (optional)
        language: User language preference (default: 'en')
        created_at: When profile was created (auto-managed)
        updated_at: When profile was last updated (auto-managed)

    Relationships:
        user: The user this profile belongs to

    Example:
        >>> # Create user profile
        >>> profile = UserProfile(
        ...     user_id=user_id,
        ...     name="John Doe",
        ...     bio="Software engineer",
        ...     language="en"
        ... )
        >>> session.add(profile)
        >>> await session.commit()
        >>>
        >>> # Check if user has profile
        >>> result = await session.execute(
        ...     select(UserProfile).where(UserProfile.user_id == user_id)
        ... )
        >>> profile = result.scalar_one_or_none()
        >>> has_profile = profile is not None
        >>>
        >>> # Update profile
        >>> profile.name = "Jane Doe"
        >>> await session.commit()

    Note:
        - Presence of record indicates user has profile
        - No record means user has no profile (not an error)
        - name is required when profile exists
        - Other fields can be added as needed (bio, phone, etc.)
    """

    __tablename__ = "user_profile"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        comment="User ID (also primary key)",
    )
    name = Column(Text, nullable=False, comment="User display name")
    bio = Column(Text, nullable=True, comment="User biography")
    avatar_url = Column(Text, nullable=True, comment="URL to user avatar image")
    timezone = Column(
        Text, nullable=True, comment="User timezone (e.g., 'UTC', 'America/New_York')"
    )
    language = Column(
        Text,
        nullable=False,
        default="en",
        comment="User language preference (ISO 639-1 code)",
    )

    # Relationship
    user = relationship("User", back_populates="profile")

    __table_args__ = (Index("user_profile_name_idx", "name"),)


class UserLoginPassword(BaseModel):
    """
    Password-based authentication credentials.

    This table stores email and hashed password for password-based authentication.
    By separating authentication from identity, we can easily add other authentication
    methods (OAuth, LINE, etc.) in the future without modifying the User table.

    Attributes:
        id: Unique credential record ID (auto-increment)
        user_id: FK to users
        email: User email address (unique, used for login)
        hashed_password: Bcrypt hashed password
        password_algorithm: Hash algorithm used (default: 'bcrypt')
        created_at: When credentials were created (auto-managed)
        updated_at: When credentials were last updated (auto-managed)

    Relationships:
        user: The user these credentials belong to

    Example:
        >>> # Create password authentication
        >>> from passlib.hash import bcrypt
        >>> hashed = bcrypt.hash("user_password")
        >>> auth = UserLoginPassword(
        ...     user_id=user_id,
        ...     email="user@example.com",
        ...     hashed_password=hashed
        ... )
        >>> session.add(auth)
        >>> await session.commit()
        >>>
        >>> # Authenticate user by email
        >>> result = await session.execute(
        ...     select(UserLoginPassword)
        ...     .where(UserLoginPassword.email == email)
        ... )
        >>> auth = result.scalar_one_or_none()
        >>> if auth and bcrypt.verify(password, auth.hashed_password):
        ...     # Login successful
        ...     user_id = auth.user_id
        >>>
        >>> # Change password
        >>> auth.hashed_password = bcrypt.hash("new_password")
        >>> await session.commit()

    Note:
        - email is unique across all users (login identifier)
        - hashed_password never stores plain text
        - password_algorithm allows future algorithm changes
        - Separate table enables multiple auth methods per user
    """

    __tablename__ = "user_login_password"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="Unique credential record ID",
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="User ID",
    )
    email = Column(
        Text, nullable=False, unique=True, comment="Email address (login identifier)"
    )
    hashed_password = Column(Text, nullable=False, comment="Bcrypt hashed password")
    password_algorithm = Column(
        Text, nullable=False, default="bcrypt", comment="Hash algorithm used"
    )

    # Relationship
    user = relationship("User", back_populates="login_password")

    __table_args__ = (
        UniqueConstraint("email", name="user_login_password_email_unique"),
        Index("user_login_password_user_id_idx", "user_id"),
    )


class UserActiveStatus(BaseModel):
    """
    Active users tracking using presence-based state management.

    This table uses the "presence = state" pattern. If a record exists for
    a user, that user is active. No record means inactive. This approach
    avoids nullable columns and boolean flags.

    Attributes:
        user_id: FK to users (primary key)
        created_at: When the user was activated (inherited, semantically "activated_at")

    Relationships:
        user: The user this status belongs to

    Example:
        >>> # Activate user
        >>> status = UserActiveStatus(user_id=user_id)
        >>> session.add(status)
        >>> await session.commit()
        >>>
        >>> # Check if active
        >>> result = await session.execute(
        ...     select(UserActiveStatus)
        ...     .where(UserActiveStatus.user_id == user_id)
        ... )
        >>> is_active = result.scalar_one_or_none() is not None
        >>>
        >>> # Deactivate user
        >>> await session.delete(status)
        >>> await session.commit()

    Note:
        - No updated_at needed for status table (state is binary)
        - Activation timestamp is stored in created_at
        - To deactivate, simply delete the record
        - Inactive users cannot login
    """

    __tablename__ = "user_active_status"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        comment="User ID (also primary key)",
    )

    # Override BaseModel to remove updated_at (not needed for status table)
    updated_at = None

    # Relationship
    user = relationship("User", back_populates="active_status")


class UserArchive(BaseModel):
    """
    User archives (soft delete pattern).

    This table implements soft deletion for users. Instead of permanently
    deleting users, we create an archive record that preserves the deletion
    context and audit trail. The actual user record remains in the database
    for referential integrity and historical queries.

    Attributes:
        user_id: FK to users (primary key)
        reason: Reason for archiving (required for audit)
        archived_by: FK to users (who performed the archiving)
        created_at: When user was archived (inherited, semantically "archived_at")
        updated_at: When archive record was last updated

    Relationships:
        user: The archived user
        archiver: User who performed the archiving

    Example:
        >>> # Archive user
        >>> archive = UserArchive(
        ...     user_id=user_id,
        ...     reason="User requested account deletion",
        ...     archived_by=user_id  # self-deletion
        ... )
        >>> session.add(archive)
        >>> await session.commit()
        >>>
        >>> # Check if archived
        >>> result = await session.execute(
        ...     select(UserArchive)
        ...     .where(UserArchive.user_id == user_id)
        ... )
        >>> is_archived = result.scalar_one_or_none() is not None
        >>>
        >>> # List non-archived users
        >>> result = await session.execute(
        ...     select(User)
        ...     .outerjoin(UserArchive)
        ...     .where(UserArchive.user_id.is_(None))
        ... )
        >>> active_users = result.scalars().all()

    Note:
        - Soft delete: user record is not deleted from database
        - Presence of archive record indicates deleted state
        - Always include reason for compliance
        - created_at semantically represents "archived_at"
        - Archived users cannot login
    """

    __tablename__ = "user_archives"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        comment="Archived user ID (also primary key)",
    )
    reason = Column(Text, nullable=False, comment="Reason for archiving (audit trail)")
    archived_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        comment="User who performed the archiving",
    )

    # Relationships
    user = relationship("User", back_populates="archive", foreign_keys=[user_id])
    archiver = relationship("User", foreign_keys=[archived_by])


__all__ = [
    "User",
    "UserProfile",
    "UserLoginPassword",
    "UserActiveStatus",
    "UserArchive",
]
