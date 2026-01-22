"""
Device Models

Contains Device and DeviceHeartbeat models.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Column,
    Enum,
    String,
    Text,
    Integer,
    Numeric,
    BigInteger,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils.compat import UUID as pyUUID

from app.db.base import Base
from app.models import SoftDeleteMixin, TimestampMixin, OrganizationMixin


class HardwareType:
    """Hardware type constants for different display devices."""

    LOOKING_GLASS_PORTRAIT = "looking_glass_portrait"
    LOOKING_GLASS_65 = "looking_glass_65"
    LOOKING_GLASS_32 = "looking_glass_32"
    HYPERVSN_SOLO = "hypervsn_solo"
    HYPERVSN_3D_WALL = "hypervsn_3d_wall"
    CUSTOM_LED_FAN = "custom_led_fan"
    WEB_EMULATOR = "web_emulator"


class DeviceStatus:
    """Device status constants."""

    PENDING = "pending"
    ACTIVE = "active"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    DECOMMISSIONED = "decommissioned"


class Device(Base, TimestampMixin, SoftDeleteMixin, OrganizationMixin):
    """
    Device model representing a holographic display.

    Devices are registered to organizations and can play content
    from playlists. Each device has unique hardware identification
    and reports status via heartbeats.
    """

    __tablename__ = "devices"

    # Primary key
    id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=pyUUID.uuid4,
    )

    # Basic info
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Hardware Identity
    hardware_type: Mapped[str] = mapped_column(
        Enum(
            HardwareType.LOOKING_GLASS_PORTRAIT,
            HardwareType.LOOKING_GLASS_65,
            HardwareType.LOOKING_GLASS_32,
            HardwareType.HYPERVSN_SOLO,
            HardwareType.HYPERVSN_3D_WALL,
            HardwareType.CUSTOM_LED_FAN,
            HardwareType.WEB_EMULATOR,
            name="hardware_type",
        ),
        nullable=False,
        index=True,
    )
    hardware_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )  # MAC address or TPM attestation hash
    device_secret_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )  # Argon2id hash of pre-shared key

    # Status & Health
    status: Mapped[str] = mapped_column(
        Enum(
            DeviceStatus.PENDING,
            DeviceStatus.ACTIVE,
            DeviceStatus.OFFLINE,
            DeviceStatus.MAINTENANCE,
            DeviceStatus.DECOMMISSIONED,
            name="device_status",
        ),
        default=DeviceStatus.PENDING,
        nullable=False,
        index=True,
    )
    last_heartbeat: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    consecutive_failures: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Location & Metadata
    location_metadata: Mapped[dict] = mapped_column(
        JSON,
        default={},
        nullable=False,
    )
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=[],
        nullable=False,
    )

    # Display Configuration
    display_config: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    # Network Info
    network_info: Mapped[dict] = mapped_column(
        JSON,
        default={},
        nullable=False,
    )

    # Firmware/Software Versions
    firmware_version: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    client_version: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Current Playback State
    current_playlist_id: Mapped[Optional[pyUUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("playlists.id", ondelete="SET NULL"),
        nullable=True,
    )
    current_asset_id: Mapped[Optional[pyUUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="SET NULL"),
        nullable=True,
    )
    playback_position: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Storage Management
    storage_capacity_gb: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    storage_used_gb: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0,
        nullable=False,
    )

    # Relationships
    organization = relationship("Organization", back_populates="devices")
    current_playlist = relationship("Playlist", foreign_keys=[current_playlist_id])
    current_asset = relationship("Asset", foreign_keys=[current_asset_id])
    device_playlists = relationship("DevicePlaylist", back_populates="device", cascade="all, delete-orphan")
    heartbeats = relationship("DeviceHeartbeat", back_populates="device", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Device(id={self.id}, name={self.name}, status={self.status})>"

    # =============================================================================
    # Status Management
    # =============================================================================
    @property
    def is_online(self) -> bool:
        """Check if device is currently online based on heartbeat."""
        if self.last_heartbeat is None:
            return False
        from datetime import timedelta

        threshold = timedelta(minutes=5)
        return datetime.now() - self.last_heartbeat < threshold

    @property
    def is_active(self) -> bool:
        """Check if device is in active status."""
        return self.status == DeviceStatus.ACTIVE

    @property
    def storage_usage_percent(self) -> float:
        """Get storage usage as a percentage."""
        if self.storage_capacity_gb is None or self.storage_capacity_gb == 0:
            return 0.0
        return (float(self.storage_used_gb) / self.storage_capacity_gb) * 100

    def update_heartbeat(
        self,
        cpu_percent: Optional[float] = None,
        memory_percent: Optional[float] = None,
        storage_used: Optional[float] = None,
        temperature: Optional[int] = None,
        bandwidth_mbps: Optional[int] = None,
        latency_ms: Optional[int] = None,
        current_playlist: Optional[pyUUID] = None,
        current_asset: Optional[pyUUID] = None,
        playback_position: Optional[int] = None,
    ) -> None:
        """
        Update device heartbeat information.

        Note: Extra metrics (cpu_percent, memory_percent, temperature, etc.)
        are typically stored in DeviceHeartbeat time-series table.
        This method updates the Device's current state.
        """
        self.last_heartbeat = datetime.now()
        self.consecutive_failures = 0

        if storage_used is not None:
            self.storage_used_gb = storage_used
        if current_playlist is not None:
            self.current_playlist_id = current_playlist
        if current_asset is not None:
            self.current_asset_id = current_asset
        if playback_position is not None:
            self.playback_position = playback_position

        if self.status in [DeviceStatus.OFFLINE, DeviceStatus.PENDING]:
            self.status = DeviceStatus.ACTIVE

    def mark_offline(self) -> None:
        """Mark device as offline due to missed heartbeats."""
        self.consecutive_failures += 1
        if self.consecutive_failures >= 3:
            self.status = DeviceStatus.OFFLINE

    def activate(self) -> None:
        """Activate device after registration."""
        self.status = DeviceStatus.ACTIVE
        self.consecutive_failures = 0

    def decommission(self) -> None:
        """Decommission device from service."""
        self.status = DeviceStatus.DECOMMISSIONED

    def set_maintenance(self) -> None:
        """Set device to maintenance mode."""
        self.status = DeviceStatus.MAINTENANCE

    # =============================================================================
    # Display Configuration
    # =============================================================================
    @property
    def resolution(self) -> dict:
        """Get display resolution."""
        return self.display_config.get("resolution", {})

    @property
    def orientation(self) -> str:
        """Get display orientation (portrait/landscape)."""
        return self.display_config.get("orientation", "portrait")

    @property
    def quilt_format(self) -> dict:
        """Get quilt format configuration."""
        return self.display_config.get("quilt_format", {})

    @property
    def brightness(self) -> int:
        """Get display brightness (0-100)."""
        return self.display_config.get("brightness", 80)

    # =============================================================================
    # Location
    # =============================================================================
    @property
    def store_id(self) -> Optional[str]:
        """Get store ID from location metadata."""
        return self.location_metadata.get("store_id")

    @property
    def address(self) -> Optional[str]:
        """Get device address."""
        return self.location_metadata.get("address")

    @property
    def timezone(self) -> str:
        """Get device timezone."""
        return self.location_metadata.get("timezone", "America/New_York")

    # =============================================================================
    # Tags
    # =============================================================================
    def add_tag(self, tag: str) -> None:
        """Add a tag to the device."""
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the device."""
        if tag in self.tags:
            self.tags.remove(tag)

    def has_tag(self, tag: str) -> bool:
        """Check if device has a specific tag."""
        return tag in self.tags


class DeviceHeartbeat(Base):
    """
    Device heartbeat time-series data.

    This table should be converted to a TimescaleDB hypertable
    for efficient time-series queries and automatic data retention.
    """

    __tablename__ = "device_heartbeats"

    # Time-series timestamp (primary key for TimescaleDB)
    time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        default=datetime.now,
        nullable=False,
    )

    # Device reference (part of composite key for TimescaleDB)
    device_id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        index=True,
    )

    # System Health
    cpu_usage_percent: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    memory_usage_percent: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    storage_used_gb: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    temperature_celsius: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Network Metrics
    bandwidth_mbps: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    latency_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    packet_loss_percent: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    # Playback State
    current_playlist_id: Mapped[Optional[pyUUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    current_asset_id: Mapped[Optional[pyUUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    playback_position_sec: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Errors
    error_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    last_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    device = relationship("Device", back_populates="heartbeats")

    def __repr__(self) -> str:
        return f"<DeviceHeartbeat(time={self.time}, device_id={self.device_id})>"

    @property
    def is_healthy(self) -> bool:
        """Check if device is healthy based on metrics."""
        if self.cpu_usage_percent and self.cpu_usage_percent > 90:
            return False
        if self.memory_usage_percent and self.memory_usage_percent > 90:
            return False
        if self.temperature_celsius and self.temperature_celsius > 70:
            return False
        if self.error_count > 0:
            return False
        return True

    @property
    def health_score(self) -> float:
        """Calculate overall health score (0-100)."""
        score = 100.0

        if self.cpu_usage_percent:
            score -= max(0, (self.cpu_usage_percent - 50) * 2)

        if self.memory_usage_percent:
            score -= max(0, (self.memory_usage_percent - 50) * 2)

        if self.temperature_celsius and self.temperature_celsius > 60:
            score -= (self.temperature_celsius - 60) * 5

        score -= self.error_count * 10

        return max(0, min(100, score))
