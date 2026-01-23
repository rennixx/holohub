"""
Playlist Schemas

Pydantic schemas for playlist validation and serialization.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from uuid_utils.compat import UUID as pyUUID


# =============================================================================
# Base Schemas
# =============================================================================
class PlaylistBase(BaseModel):
    """Base playlist schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    loop_mode: bool = True
    shuffle: bool = False
    transition_type: str = Field(
        default="fade",
        pattern="^(fade|cut|slide_left|slide_right|zoom)$",
    )
    transition_duration_ms: int = Field(default=500, ge=0, le=5000)


# =============================================================================
# Schedule Configuration
# =============================================================================
class ScheduleConfig(BaseModel):
    """Playlist schedule configuration."""

    start_date: Optional[str] = None  # ISO 8601 datetime
    end_date: Optional[str] = None  # ISO 8601 datetime
    recurrence: Optional["RecurrenceConfig"] = None
    timezone: str = Field(default="America/New_York")
    priority: int = Field(default=1, ge=0, le=10)


class RecurrenceConfig(BaseModel):
    """Recurrence configuration."""

    type: Optional[str] = Field(None, pattern="^(daily|weekly|monthly|custom)$")
    interval: int = Field(default=1, ge=1)
    days_of_week: Optional[list[int]] = Field(None, min_items=1, max_items=7)  # ISO 8601
    time_ranges: list[dict] = Field(
        default_factory=list,
        # Example: [{"start": "09:00", "end": "12:00"}, {"start": "14:00", "end": "21:00"}]
    )


# =============================================================================
# Playlist Item Schemas
# =============================================================================
class PlaylistItemCreate(BaseModel):
    """Schema for adding item to playlist."""

    asset_id: pyUUID
    position: Optional[int] = Field(None, ge=0)
    duration_seconds: int = Field(default=10, ge=1)
    transition_override: Optional[str] = Field(
        None,
        pattern="^(fade|cut|slide_left|slide_right|zoom)$",
    )
    custom_settings: dict = Field(default_factory=dict)


class PlaylistItemUpdate(BaseModel):
    """Schema for updating playlist item."""

    duration_seconds: Optional[int] = Field(None, ge=1)
    transition_override: Optional[str] = None
    custom_settings: Optional[dict] = None


class PlaylistItemResponse(BaseModel):
    """Schema for playlist item response."""

    model_config = ConfigDict(from_attributes=True)

    id: pyUUID
    playlist_id: pyUUID
    asset_id: pyUUID
    position: int
    duration_seconds: int
    transition_override: Optional[str]
    custom_settings: dict
    created_at: datetime

    # Include asset summary
    asset: "AssetListItem"


# =============================================================================
# Create Schemas
# =============================================================================
class PlaylistCreate(PlaylistBase):
    """Schema for creating a new playlist."""

    schedule_config: Optional[ScheduleConfig] = None
    items: list[PlaylistItemCreate] = Field(default_factory=list, min_length=1)


# =============================================================================
# Update Schemas
# =============================================================================
class PlaylistUpdate(BaseModel):
    """Schema for updating a playlist."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    loop_mode: Optional[bool] = None
    shuffle: Optional[bool] = None
    transition_type: Optional[str] = None
    transition_duration_ms: Optional[int] = None
    schedule_config: Optional[ScheduleConfig] = None
    items: Optional[list[PlaylistItemCreate]] = None


class PlaylistItemsUpdate(BaseModel):
    """Schema for updating playlist items (reorder/replace)."""

    items: list[PlaylistItemCreate]


# =============================================================================
# Assignment Schemas
# =============================================================================
class PlaylistAssignRequest(BaseModel):
    """Schema for assigning playlist to devices."""

    device_ids: list[pyUUID] = Field(..., min_length=1)
    schedule_override: Optional[ScheduleConfig] = None


class PlaylistUnassignRequest(BaseModel):
    """Schema for unassigning playlist from devices."""

    device_ids: list[pyUUID] = Field(..., min_length=1)


# =============================================================================
# Response Schemas
# =============================================================================
class PlaylistResponse(PlaylistBase):
    """Schema for playlist response."""

    model_config = ConfigDict(from_attributes=True)

    id: pyUUID
    organization_id: pyUUID
    is_active: bool
    schedule_config: Optional[ScheduleConfig]
    total_duration_sec: Optional[int]
    item_count: int
    created_by: Optional[pyUUID]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


class PlaylistWithItemsResponse(PlaylistResponse):
    """Schema for playlist response with items."""

    items: list[PlaylistItemResponse]
    devices: list["DeviceResponse"]  # Devices assigned to this playlist
    device_count: int


# =============================================================================
# Forward references for type hints
# =============================================================================
from app.schemas.asset import AssetListItem
from app.schemas.device import DeviceResponse
