"""
Asset Models

Contains Asset and AssetAnalytics models for managing holographic assets.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, String, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid4
from uuid_utils.compat import UUID as pyUUID

from app.db.base import Base
from app.models import SoftDeleteMixin, TimestampMixin, OrganizationMixin


class AssetStatus:
    """Asset status constants."""

    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"
    DELETED = "deleted"


class Asset(Base, TimestampMixin, SoftDeleteMixin, OrganizationMixin):
    """
    Asset model representing a holographic asset.

    Assets are 3D models, images, videos, or other content
    that can be displayed on holographic devices.

    Attributes:
        name: Display name of the asset
        description: Optional description
        file_path: S3/MinIO storage key for the asset file
        file_size: Size of the file in bytes
        file_format: File format (glb, gltf, obj, fbx, usdz, etc.)
        status: Processing status (uploading, processing, ready, error)
        thumbnail_url: Optional CDN URL for thumbnail
        metadata: Additional asset metadata (dimensions, etc.)
        created_by: User who uploaded the asset
    """

    __tablename__ = "assets"

    # Primary key
    id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Basic info
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # File info
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )  # S3/MinIO storage key
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )  # Size in bytes
    file_format: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # glb, gltf, obj, fbx, usdz, etc.

    # Status
    status: Mapped[str] = mapped_column(
        Enum(
            AssetStatus.UPLOADING,
            AssetStatus.PROCESSING,
            AssetStatus.READY,
            AssetStatus.ERROR,
            AssetStatus.DELETED,
            name="asset_status",
        ),
        default=AssetStatus.UPLOADING,
        nullable=False,
        index=True,
    )

    # Optional thumbnail
    thumbnail_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Additional metadata
    asset_metadata: Mapped[dict] = mapped_column(
        JSON,
        default={},
        nullable=False,
    )  # Dimensions, polygons, etc.

    # Who uploaded it
    created_by_id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    analytics = relationship("AssetAnalytics", back_populates="asset", cascade="all, delete-orphan")
    playlist_items = relationship("PlaylistItem", back_populates="asset", cascade="all, delete-orphan")
    uploaded_by = relationship("User", back_populates="created_assets", foreign_keys=[created_by_id])
    organization = relationship("Organization", back_populates="assets")

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, name={self.name}, status={self.status})>"


class AssetAnalytics(Base):
    """
    Asset analytics time-series data.

    This table should be converted to a TimescaleDB hypertable
    for tracking asset views, downloads, and playback.

    Attributes:
        time: Timestamp of the event
        asset_id: Reference to the asset
        device_id: Reference to the device
        org_id: Reference to the organization
        event_type: Type of event (view/download/error)
        duration_sec: How long asset was displayed
        location_data: Location metadata at time of event
        user_agent: Web viewer user agent
    """

    __tablename__ = "asset_analytics"

    # Time-series timestamp (primary key for TimescaleDB)
    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        default=datetime.now,
        nullable=False,
    )

    # Asset reference (part of composite key for TimescaleDB)
    asset_id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        index=True,
    )

    # Device reference
    device_id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        index=True,
    )

    # Organization reference
    org_id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )

    # Event Details
    event_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )  # 'view', 'download', 'error'
    duration_sec: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )  # How long was it displayed

    # Context
    location_data: Mapped[dict] = mapped_column(
        JSON,
        default={},
        nullable=False,
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )  # For web viewers

    # Relationships
    asset = relationship("Asset", back_populates="analytics")
    device = relationship("Device")

    def __repr__(self) -> str:
        return f"<AssetAnalytics(time={self.time}, asset_id={self.asset_id}, event_type={self.event_type})>"
