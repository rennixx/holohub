"""
Playlist Models

Contains Playlist, PlaylistItem, and DevicePlaylist models.
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
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid4
from uuid_utils.compat import UUID as pyUUID

from app.db.base import Base
from app.models import SoftDeleteMixin, TimestampMixin, OrganizationMixin


class TransitionType:
    """Playlist transition type constants."""

    FADE = "fade"
    CUT = "cut"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    ZOOM = "zoom"


class Playlist(Base, TimestampMixin, SoftDeleteMixin, OrganizationMixin):
    """
    Playlist model representing a sequence of assets for display.

    Playlists define what content plays on devices, in what order,
    and with what transitions. They support scheduling and recurrence.

    Attributes:
        id: Unique playlist identifier
        name: Playlist display name
        description: Playlist description
        loop_mode: Whether to loop the playlist
        shuffle: Whether to shuffle items
        transition_type: Default transition between assets
        transition_duration_ms: Transition duration in milliseconds
        schedule_config: JSON scheduling configuration
        is_active: Whether playlist is currently active
        total_duration_sec: Total duration of all items
        item_count: Number of items in playlist
        created_by: User who created the playlist
    """

    __tablename__ = "playlists"

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
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Playback Settings
    loop_mode: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    shuffle: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    transition_type: Mapped[str] = mapped_column(
        Enum(
            TransitionType.FADE,
            TransitionType.CUT,
            TransitionType.SLIDE_LEFT,
            TransitionType.SLIDE_RIGHT,
            TransitionType.ZOOM,
            name="transition_type",
        ),
        default=TransitionType.FADE,
        nullable=False,
    )
    transition_duration_ms: Mapped[int] = mapped_column(
        Integer,
        default=500,
        nullable=False,
    )

    # Scheduling
    schedule_config: Mapped[dict] = mapped_column(
        JSON,
        default={},
        nullable=False,
    )  # {"start_date": "...", "end_date": "...", "recurrence": {...}, "timezone": "..."}

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )
    total_duration_sec: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    item_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Created by
    created_by: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    organization = relationship("Organization", back_populates="playlists")
    creator = relationship("User", back_populates="created_playlists", foreign_keys=[created_by])
    items = relationship("PlaylistItem", back_populates="playlist", cascade="all, delete-orphan")
    device_playlists = relationship("DevicePlaylist", back_populates="playlist", cascade="all, delete-orphan")

    # Devices where this is the current playlist
    devices_current = relationship(
        "Device",
        foreign_keys="Device.current_playlist_id",
        back_populates="current_playlist",
    )

    def __repr__(self) -> str:
        return f"<Playlist(id={self.id}, name={self.name}, items={self.item_count})>"

    # =============================================================================
    # Items Management
    # =============================================================================
    def add_item(
        self,
        asset_id: pyUUID,
        position: Optional[int] = None,
        duration_seconds: int = 10,
        transition_override: Optional[str] = None,
    ) -> "PlaylistItem":
        """
        Add an item to the playlist.

        Args:
            asset_id: Asset to add
            position: Position in playlist (default: append)
            duration_seconds: How long to show asset
            transition_override: Override default transition

        Returns:
            Created PlaylistItem
        """
        from app.models.playlist import PlaylistItem

        if position is None:
            position = self.item_count

        item = PlaylistItem(
            playlist_id=self.id,
            asset_id=asset_id,
            position=position,
            duration_seconds=duration_seconds,
            transition_override=transition_override,
        )
        self.item_count += 1
        self._update_total_duration()
        return item

    def remove_item(self, item_id: pyUUID) -> None:
        """
        Remove an item from the playlist.

        Args:
            item_id: Item to remove
        """
        for item in self.items:
            if item.id == item_id:
                self.items.remove(item)
                self.item_count -= 1
                # Reorder remaining items
                for i, remaining in enumerate(self.items):
                    if remaining.position > item.position:
                        remaining.position = i
                self._update_total_duration()
                break

    def reorder_items(self, item_ids: list[pyUUID]) -> None:
        """
        Reorder all items in playlist.

        Args:
            item_ids: New order of item IDs
        """
        item_map = {item.id: item for item in self.items}
        for position, item_id in enumerate(item_ids):
            if item_id in item_map:
                item_map[item_id].position = position

    def _update_total_duration(self) -> None:
        """Recalculate total duration from items."""
        self.total_duration_sec = sum(item.duration_seconds for item in self.items)

    # =============================================================================
    # Scheduling
    # =============================================================================
    @property
    def has_schedule(self) -> bool:
        """Check if playlist has a schedule configured."""
        return bool(self.schedule_config.get("start_date"))

    @property
    def schedule_start(self) -> Optional[datetime]:
        """Get schedule start datetime."""
        start_str = self.schedule_config.get("start_date")
        if start_str:
            return datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        return None

    @property
    def schedule_end(self) -> Optional[datetime]:
        """Get schedule end datetime."""
        end_str = self.schedule_config.get("end_date")
        if end_str:
            return datetime.fromisoformat(end_str.replace("Z", "+00:00"))
        return None

    @property
    def is_scheduled_now(self) -> bool:
        """Check if playlist is currently scheduled to play."""
        if not self.has_schedule or not self.is_active:
            return False

        now = datetime.now()
        start = self.schedule_start
        end = self.schedule_end

        if start and now < start:
            return False
        if end and now > end:
            return False

        # Check recurrence
        recurrence = self.schedule_config.get("recurrence", {})
        if recurrence:
            return self._check_recurrence(now, recurrence)

        return True

    def _check_recurrence(self, now: datetime, recurrence: dict) -> bool:
        """
        Check if current time matches recurrence rules.

        Args:
            now: Current datetime
            recurrence: Recurrence configuration

        Returns:
            True if scheduled now
        """
        import pytz

        timezone_str = self.schedule_config.get("timezone", "America/New_York")
        tz = pytz.timezone(timezone_str)
        now_local = now.astimezone(tz)

        # Check day of week
        days_of_week = recurrence.get("days_of_week", [])  # ISO 8601 (1=Monday, 7=Sunday)
        if days_of_week:
            if now_local.isoweekday() not in days_of_week:
                return False

        # Check time ranges
        time_ranges = recurrence.get("time_ranges", [])
        if time_ranges:
            current_time = now_local.strftime("%H:%M")
            for time_range in time_ranges:
                start = time_range.get("start", "00:00")
                end = time_range.get("end", "23:59")
                if start <= current_time <= end:
                    return True
            return False

        return True


class PlaylistItem(Base):
    """
    Playlist Item model representing an asset in a playlist.

    Junction table between playlists and assets with ordering
    and per-item configuration.

    Attributes:
        id: Unique item identifier
        playlist_id: Reference to playlist
        asset_id: Reference to asset
        position: Display order (0-indexed)
        duration_seconds: How long to show this asset
        transition_override: Override playlist default transition
        custom_settings: Per-item display settings
    """

    __tablename__ = "playlist_items"

    # Primary key
    id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Foreign keys
    playlist_id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("playlists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assets.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Ordering
    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Duration
    duration_seconds: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )

    # Per-item overrides
    transition_override: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    custom_settings: Mapped[dict] = mapped_column(
        JSON,
        default={},
        nullable=False,
    )  # {"brightness": 90, "rotation": 90}

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        nullable=False,
    )

    # Relationships
    playlist = relationship("Playlist", back_populates="items")
    asset = relationship("Asset", back_populates="playlist_items")

    # Unique constraint on playlist_id + position
    __table_args__ = (
        UniqueConstraint("playlist_id", "position", name="uq_playlist_position"),
    )

    def __repr__(self) -> str:
        return f"<PlaylistItem(id={self.id}, playlist_id={self.playlist_id}, position={self.position})>"


class DevicePlaylist(Base):
    """
    Device Playlist model (many-to-many).

    Associates playlists with devices, allowing per-device
    schedule overrides.

    Attributes:
        id: Unique identifier
        device_id: Reference to device
        playlist_id: Reference to playlist
        assigned_at: When assignment was created
        assigned_by: User who made the assignment
        schedule_override: Override playlist schedule for this device
    """

    __tablename__ = "device_playlists"

    # Primary key
    id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Foreign keys
    device_id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    playlist_id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("playlists.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Assignment metadata
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        nullable=False,
    )
    assigned_by: Mapped[Optional[pyUUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Override playlist schedule for this specific device
    schedule_override: Mapped[dict] = mapped_column(
        JSON,
        default={},
        nullable=False,
    )

    # Relationships
    device = relationship("Device", back_populates="device_playlists")
    playlist = relationship("Playlist", back_populates="device_playlists")

    # Unique constraint on device_id + playlist_id
    __table_args__ = (
        UniqueConstraint("device_id", "playlist_id", name="uq_device_playlist"),
    )

    def __repr__(self) -> str:
        return f"<DevicePlaylist(device_id={self.device_id}, playlist_id={self.playlist_id})>"
