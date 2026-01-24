"""
Audit Log Model

Tracks all mutations for compliance and security auditing.
"""
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid4
from uuid_utils.compat import UUID as pyUUID

from app.db.base import Base


class AuditLog(Base):
    """
    Audit log for compliance and security.

    Tracks all mutations to data for SOC 2 Type II compliance
    and security monitoring.

    Attributes:
        id: Unique log entry identifier
        timestamp: When the action occurred
        user_id: User who performed the action
        org_id: Organization context
        ip_address: IP address of request
        user_agent: User agent string
        action: Action performed (user.login, asset.upload, etc.)
        resource_type: Type of resource affected
        resource_id: ID of resource affected
        changes: Before/after values for updates
        metadata: Additional context
        success: Whether action succeeded
        error_message: Error message if failed
    """

    __tablename__ = "audit_logs"

    # Primary key
    id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        nullable=False,
        index=True,
    )

    # Who
    user_id: Mapped[Optional[pyUUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    org_id: Mapped[Optional[pyUUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        INET,
        nullable=True,
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # What
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )  # 'user.login', 'asset.upload', 'device.command', 'playlist.update'
    resource_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )  # 'user', 'asset', 'device', 'playlist'
    resource_id: Mapped[Optional[pyUUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # Details
    changes: Mapped[dict] = mapped_column(
        JSON,
        default={},
        nullable=False,
    )  # {"before": {"status": "offline"}, "after": {"status": "active"}}
    audit_metadata: Mapped[dict] = mapped_column(
        JSON,
        default={},
        nullable=False,
    )  # Additional context

    # Result
    success: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, resource_type={self.resource_type})>"

    # =============================================================================
    # Common Actions
    # =============================================================================
    class Actions:
        """Common audit action constants."""

        # Auth
        USER_LOGIN = "user.login"
        USER_LOGOUT = "user.logout"
        USER_REGISTER = "user.register"
        USER_PASSWORD_CHANGE = "user.password_change"
        USER_PASSWORD_RESET = "user.password_reset"
        USER_MFA_ENABLED = "user.mfa_enabled"
        USER_MFA_DISABLED = "user.mfa_disabled"

        # User management
        USER_CREATED = "user.created"
        USER_UPDATED = "user.updated"
        USER_DELETED = "user.deleted"
        USER_ROLE_CHANGED = "user.role_changed"

        # Organization
        ORG_CREATED = "org.created"
        ORG_UPDATED = "org.updated"
        ORG_DELETED = "org.deleted"
        ORG_TIER_CHANGED = "org.tier_changed"

        # Device
        DEVICE_REGISTERED = "device.registered"
        DEVICE_ACTIVATED = "device.activated"
        DEVICE_UPDATED = "device.updated"
        DEVICE_DELETED = "device.deleted"
        DEVICE_COMMAND = "device.command"

        # Asset
        ASSET_UPLOADED = "asset.uploaded"
        ASSET_UPDATED = "asset.updated"
        ASSET_DELETED = "asset.deleted"
        ASSET_REPROCESSED = "asset.reprocessed"
        ASSET_DOWNLOADED = "asset.downloaded"

        # Playlist
        PLAYLIST_CREATED = "playlist.created"
        PLAYLIST_UPDATED = "playlist.updated"
        PLAYLIST_DELETED = "playlist.deleted"
        PLAYLIST_ASSIGNED = "playlist.assigned"
        PLAYLIST_UNASSIGNED = "playlist.unassigned"

    class ResourceTypes:
        """Resource type constants."""

        USER = "user"
        ORGANIZATION = "organization"
        DEVICE = "device"
        ASSET = "asset"
        PLAYLIST = "playlist"
        PLAYLIST_ITEM = "playlist_item"

    @classmethod
    def create(
        cls,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[pyUUID] = None,
        user_id: Optional[pyUUID] = None,
        org_id: Optional[pyUUID] = None,
        changes: Optional[dict] = None,
        audit_metadata: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> "AuditLog":
        """
        Create a new audit log entry.

        Args:
            action: Action performed
            resource_type: Type of resource
            resource_id: ID of resource
            user_id: User who performed action
            org_id: Organization context
            changes: Before/after values
            audit_metadata: Additional context
            ip_address: IP address
            user_agent: User agent
            success: Whether action succeeded
            error_message: Error message if failed

        Returns:
            New AuditLog instance
        """
        return cls(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            org_id=org_id,
            changes=changes or {},
            audit_metadata=audit_metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
        )
