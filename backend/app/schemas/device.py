"""
Device Schemas

Pydantic schemas for device validation and serialization.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from uuid_utils.compat import UUID as pyUUID


# =============================================================================
# Hardware Types
# =============================================================================
class HardwareType:
    """Hardware type constants."""

    LOOKING_GLASS_PORTRAIT = "looking_glass_portrait"
    LOOKING_GLASS_65 = "looking_glass_65"
    LOOKING_GLASS_32 = "looking_glass_32"
    HYPERVSN_SOLO = "hypervsn_solo"
    HYPERVSN_3D_WALL = "hypervsn_3d_wall"
    CUSTOM_LED_FAN = "custom_led_fan"
    WEB_EMULATOR = "web_emulator"


# =============================================================================
# Base Schemas
# =============================================================================
class DeviceBase(BaseModel):
    """Base device schema."""

    name: str = Field(..., min_length=1, max_length=255)
    hardware_type: str = Field(
        ...,
        pattern="^(looking_glass_portrait|looking_glass_65|looking_glass_32|hypervsn_solo|hypervsn_3d_wall|custom_led_fan|web_emulator)$",
    )
    display_config: dict = Field(
        default_factory=lambda: {
            "resolution": {"width": 1536, "height": 2048},
            "orientation": "portrait",
            "quilt_format": {"cols": 8, "rows": 6, "views": 48},
            "brightness": 80,
        }
    )
    location_metadata: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


# =============================================================================
# Create Schemas
# =============================================================================
class DeviceRegister(DeviceBase):
    """Schema for registering a new device."""

    hardware_id: str = Field(..., min_length=12, max_length=255)
    device_secret: str = Field(..., min_length=16, max_length=255)

    @field_validator("hardware_id")
    @classmethod
    def validate_hardware_id(cls, v: str) -> str:
        """Validate hardware ID format (MAC address or TPM hash)."""
        import re

        # Check for MAC address format
        mac_pattern = r"^([A-F0-9]{2}:){5}[A-F0-9]{2}$"
        if re.match(mac_pattern, v.upper()):
            return v.upper()

        # Check for TPM hash format (hex string)
        if re.match(r"^[A-F0-9]{64}$", v):
            return v.upper()

        raise ValueError(
            "hardware_id must be a MAC address (XX:XX:XX:XX:XX:XX) "
            "or TPM hash (64-character hex string)"
        )


class DeviceActivate(BaseModel):
    """Schema for activating a device."""

    activation_code: str = Field(..., pattern=r"^[A-Z0-9]{3}-[A-Z0-9]{3}-[A-Z0-9]{3}$")


# =============================================================================
# Update Schemas
# =============================================================================
class DeviceUpdate(BaseModel):
    """Schema for updating a device."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    status: Optional[str] = Field(
        None,
        pattern="^(pending|active|offline|maintenance|decommissioned)$",
    )
    display_config: Optional[dict] = None
    location_metadata: Optional[dict] = None
    tags: Optional[list[str]] = None
    firmware_version: Optional[str] = Field(None, max_length=50)
    client_version: Optional[str] = Field(None, max_length=50)


# =============================================================================
# Command Schemas
# =============================================================================
class DeviceCommand(BaseModel):
    """Schema for sending commands to a device."""

    command: str = Field(
        ...,
        pattern="^(play|pause|stop|reboot|clear_cache|update_firmware|screenshot)$",
    )
    params: dict = Field(default_factory=dict)


class DeviceHeartbeat(BaseModel):
    """Schema for device heartbeat."""

    status: str = Field(default="playing", pattern="^(playing|paused|stopped|error)$")
    current_playlist_id: Optional[pyUUID] = None
    current_asset_id: Optional[pyUUID] = None
    playback_position_sec: Optional[int] = Field(None, ge=0)
    system_health: Optional["SystemHealth"] = None
    network_info: Optional["NetworkInfo"] = None


class SystemHealth(BaseModel):
    """System health metrics."""

    cpu_percent: Optional[float] = Field(None, ge=0, le=100)
    memory_percent: Optional[float] = Field(None, ge=0, le=100)
    storage_used_gb: Optional[float] = Field(None, ge=0)
    temperature_celsius: Optional[int] = Field(None, ge=0, le=100)


class NetworkInfo(BaseModel):
    """Network information."""

    bandwidth_mbps: Optional[int] = Field(None, ge=0)
    latency_ms: Optional[int] = Field(None, ge=0)
    ip_address: Optional[str] = None
    public_ip: Optional[str] = None


# =============================================================================
# Response Schemas
# =============================================================================
class DeviceResponse(DeviceBase):
    """Schema for device response."""

    model_config = ConfigDict(from_attributes=True)

    id: pyUUID
    organization_id: pyUUID
    hardware_id: str
    status: str
    last_heartbeat: Optional[datetime]
    consecutive_failures: int
    network_info: dict
    firmware_version: Optional[str]
    client_version: Optional[str]
    current_playlist_id: Optional[pyUUID]
    current_asset_id: Optional[pyUUID]
    playback_position: Optional[int]
    storage_capacity_gb: Optional[int]
    storage_used_gb: float
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]

    # Exclude sensitive data
    model_config = ConfigDict(from_attributes=True, exclude={"device_secret_hash"})


class DeviceStats(BaseModel):
    """Device statistics."""

    uptime_percent: float
    total_assets_played: int
    avg_playback_duration_sec: int
    error_count: int
    last_seen: Optional[datetime]


class DeviceListResponse(BaseModel):
    """Response schema for device list with stats."""

    items: list[DeviceResponse]
    stats: DeviceStats
