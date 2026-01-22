"""
User Model

Represents a user in the HoloHub system.
Users belong to organizations and have roles with specific permissions.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import EmailStr
from sqlalchemy import (
    JSON,
    Column,
    Enum,
    String,
    Text,
    Boolean,
    Integer,
    BigInteger,
    DateTime,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID, INET
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils.compat import UUID as pyUUID

from app.db.base import Base
from app.models import SoftDeleteMixin, TimestampMixin, OrganizationMixin


class UserRole:
    """User role constants."""

    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class User(Base, TimestampMixin, SoftDeleteMixin, OrganizationMixin):
    """
    User model representing a user account.

    Users belong to an organization and have a role that determines
    their permissions within that organization.

    Attributes:
        id: Unique user identifier
        email: User email address (unique globally)
        email_verified: Whether email has been verified
        password_hash: Bcrypt hash of password
        mfa_enabled: Whether multi-factor auth is enabled
        mfa_secret: Encrypted TOTP secret
        backup_codes: Hashed backup codes for MFA recovery
        full_name: User's full name
        avatar_url: URL to user avatar image
        role: User role (owner/admin/editor/viewer)
        permissions: Granular permission overrides
        last_login: Last successful login timestamp
        last_ip: Last login IP address
        failed_login_attempts: Consecutive failed login count
        locked_until: Account lockout expiration
        password_changed_at: Last password change timestamp
        force_password_reset: Whether user must reset password
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=pyUUID.uuid4,
    )

    # Authentication
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Multi-factor Auth
    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    mfa_secret: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )  # Encrypted TOTP secret
    backup_codes: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=[],
        nullable=False,
    )  # Hashed one-time recovery codes

    # Profile
    full_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Role & Permissions
    role: Mapped[str] = mapped_column(
        Enum(
            UserRole.OWNER,
            UserRole.ADMIN,
            UserRole.EDITOR,
            UserRole.VIEWER,
            name="user_role",
        ),
        default=UserRole.VIEWER,
        nullable=False,
    )
    permissions: Mapped[dict] = mapped_column(
        JSON,
        default={},
        nullable=False,
    )  # Granular permission overrides

    # Session Management
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_ip: Mapped[Optional[str]] = mapped_column(
        INET,
        nullable=True,
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Security
    password_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        nullable=False,
    )
    force_password_reset: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    organization = relationship("Organization", back_populates="users")
    created_assets = relationship("Asset", back_populates="uploaded_by", foreign_keys="Asset.created_by")
    created_playlists = relationship("Playlist", back_populates="created_by")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

    # =============================================================================
    # Authentication
    # =============================================================================
    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.locked_until is None:
            return False
        return datetime.now() < self.locked_until

    def record_failed_login(self, max_attempts: int, lockout_minutes: int) -> bool:
        """
        Record a failed login attempt.

        Args:
            max_attempts: Maximum attempts before lockout
            lockout_minutes: How long to lock account

        Returns:
            True if account is now locked
        """
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            from datetime import timedelta

            self.locked_until = datetime.now() + timedelta(minutes=lockout_minutes)
            return True
        return False

    def reset_failed_logins(self) -> None:
        """Reset failed login counter (called on successful login)."""
        self.failed_login_attempts = 0
        self.locked_until = None

    def update_last_login(self, ip_address: Optional[str] = None) -> None:
        """
        Update last login information.

        Args:
            ip_address: IP address of login
        """
        self.last_login = datetime.now()
        if ip_address:
            self.last_ip = ip_address

    # =============================================================================
    # Permissions
    # =============================================================================
    def has_permission(self, permission: str) -> bool:
        """
        Check if user has a specific permission.

        Args:
            permission: Permission to check

        Returns:
            True if user has permission
        """
        from app.core.row_level_security import has_permission

        return has_permission(self.role, permission, self.permissions)

    def can_manage_users(self) -> bool:
        """Check if user can manage other users."""
        return self.role in [UserRole.OWNER, UserRole.ADMIN]

    def can_change_role(self, target_role: str) -> bool:
        """
        Check if user can change another user's role.

        Args:
            target_role: Role to change to

        Returns:
            True if allowed
        """
        # Only owners/admins can change roles
        if self.role not in [UserRole.OWNER, UserRole.ADMIN]:
            return False

        # Can't promote someone above your own level
        from app.core.row_level_security import ROLE_HIERARCHY

        user_level = ROLE_HIERARCHY.get(self.role, 0)
        target_level = ROLE_HIERARCHY.get(target_role, 0)
        return target_level <= user_level

    # =============================================================================
    # Profile
    # =============================================================================
    @property
    def display_name(self) -> str:
        """Get user's display name."""
        return self.full_name or self.email.split("@")[0]

    @property
    def initials(self) -> str:
        """Get user's initials."""
        if self.full_name:
            parts = self.full_name.split()
            if len(parts) >= 2:
                return f"{parts[0][0]}{parts[1][0]}".upper()
            return parts[0][0].upper()
        return self.email[0].upper()

    # =============================================================================
    # MFA
    # =============================================================================
    def enable_mfa(self, secret: str, backup_codes: list[str]) -> None:
        """
        Enable multi-factor authentication.

        Args:
            secret: TOTP secret (will be encrypted)
            backup_codes: Backup codes (will be hashed)
        """
        from app.core.security import hash_backup_code

        self.mfa_enabled = True
        self.mfa_secret = secret  # Should be pre-encrypted
        self.backup_codes = [hash_backup_code(code) for code in backup_codes]

    def disable_mfa(self) -> None:
        """Disable multi-factor authentication."""
        self.mfa_enabled = False
        self.mfa_secret = None
        self.backup_codes = []

    def verify_backup_code(self, code: str) -> bool:
        """
        Verify a backup code against stored codes.

        Args:
            code: Backup code to verify

        Returns:
            True if code is valid

        Note:
            Codes are single-use and will be removed after use
        """
        from app.core.security import verify_backup_code

        for i, hashed_code in enumerate(self.backup_codes):
            if verify_backup_code(code, hashed_code):
                # Remove used code
                self.backup_codes.pop(i)
                return True
        return False
