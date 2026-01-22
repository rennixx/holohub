"""
SQLAlchemy Models Package

Contains all database models for HoloHub.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.db.base import Base


class TimestampMixin:
    """Mixin for adding timestamp fields to models."""

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        default=None,
        nullable=True,
        index=True,
    )

    def soft_delete(self) -> None:
        """Mark the record as deleted."""
        self.deleted_at = datetime.now()

    @property
    def is_deleted(self) -> bool:
        """Check if the record is deleted."""
        return self.deleted_at is not None


class OrganizationMixin:
    """
    Mixin for adding organization foreign key to models.

    All multi-tenant models should inherit from this to enable
    organization-based data isolation.
    """

    @declared_attr.directive
    def organization_id(cls) -> Mapped["uuid.UUID"]:
        """Organization foreign key."""
        return mapped_column(
            ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )


# Import all models
from app.models.asset import Asset, AssetAnalytics
from app.models.audit_log import AuditLog
from app.models.device import Device, DeviceHeartbeat
from app.models.device_playlist import DevicePlaylist
from app.models.organization import Organization
from app.models.playlist import Playlist, PlaylistItem
from app.models.user import User

__all__ = [
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",
    "OrganizationMixin",
    # Models
    "Organization",
    "User",
    "Device",
    "DeviceHeartbeat",
    "Asset",
    "AssetAnalytics",
    "Playlist",
    "PlaylistItem",
    "DevicePlaylist",
    "AuditLog",
]

import uuid
