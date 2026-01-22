"""
Device Heartbeat Model

Time-series data for device health monitoring using TimescaleDB.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Numeric,
    Integer,
    Text,
    BigInteger,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils.compat import UUID as pyUUID

from app.db.base import Base


class DeviceHeartbeat(Base):
    """
    Device heartbeat time-series data.

    This table should be converted to a TimescaleDB hypertable
    for efficient time-series queries and automatic data retention.

    Stores device health metrics including CPU, memory, storage,
    temperature, network stats, and playback state.

    Attributes:
        time: Timestamp of the heartbeat
        device_id: Reference to the device
        cpu_usage_percent: CPU usage percentage
        memory_usage_percent: Memory usage percentage
        storage_used_gb: Storage used in GB
        temperature_celsius: Device temperature
        bandwidth_mbps: Network bandwidth in Mbps
        latency_ms: Network latency in milliseconds
        packet_loss_percent: Network packet loss percentage
        current_playlist_id: Currently playing playlist
        current_asset_id: Currently playing asset
        playback_position_sec: Current playback position
        error_count: Number of errors since last heartbeat
        last_error: Last error message
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

    # =============================================================================
    # Health Metrics
    # =============================================================================
    @property
    def is_healthy(self) -> bool:
        """
        Check if device is healthy based on metrics.

        Returns:
            True if all metrics are within acceptable ranges
        """
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
        """
        Calculate overall health score (0-100).

        Returns:
            Health score based on CPU, memory, temperature, and errors
        """
        score = 100.0

        # CPU impact
        if self.cpu_usage_percent:
            score -= max(0, (self.cpu_usage_percent - 50) * 2)

        # Memory impact
        if self.memory_usage_percent:
            score -= max(0, (self.memory_usage_percent - 50) * 2)

        # Temperature impact
        if self.temperature_celsius:
            if self.temperature_celsius > 60:
                score -= (self.temperature_celsius - 60) * 5

        # Error impact
        score -= self.error_count * 10

        return max(0, min(100, score))


# Import at end to avoid circular dependency
from sqlalchemy import ForeignKey
