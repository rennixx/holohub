"""
Asset Analytics Model

Time-series data for asset usage analytics using TimescaleDB.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils.compat import UUID as pyUUID

from app.db.base import Base


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
