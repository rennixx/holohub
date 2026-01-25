"""
Devices API

Endpoints for managing holographic display devices.
"""
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, or_

from app.api.deps import CurrentUser, DBSession
from app.models import Device, DeviceStatus, Playlist, PlaylistItem, Asset
from app.core.security import hash_device_secret, verify_device_secret, create_device_token, generate_activation_code
from uuid_utils import uuid4
from uuid_utils.compat import UUID as pyUUID
import secrets
from typing import Dict, Any


router = APIRouter()


# =============================================================================
# Schemas
# =============================================================================
class PaginationMeta(BaseModel):
    """Pagination metadata matching frontend expectations."""

    total: int
    page: int
    page_size: int
    pages: int


class DeviceListResponse(BaseModel):
    """Paginated list of devices."""

    items: list[dict]
    meta: PaginationMeta


class DeviceResponse(BaseModel):
    """Single device response."""

    id: str
    name: str
    hardware_type: str
    hardware_id: str
    status: str
    last_heartbeat: Optional[str]
    location_metadata: dict
    tags: list[str]
    display_config: dict
    network_info: dict
    firmware_version: Optional[str]
    client_version: Optional[str]
    current_playlist_id: Optional[str]
    organization_id: str
    created_at: str
    updated_at: str


class DeviceRegistrationResponse(BaseModel):
    """Response for device registration including the device secret."""

    device: DeviceResponse
    device_secret: str = Field(..., description="Store this securely - needed for device authentication")


class DeviceCreate(BaseModel):
    """Schema for creating a device."""

    name: str = Field(..., max_length=255)
    hardware_type: str = Field(..., max_length=50)
    hardware_id: str = Field(..., max_length=255)
    location_metadata: dict = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class DeviceUpdate(BaseModel):
    """Schema for updating a device."""

    name: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = None
    location_metadata: Optional[dict] = None
    tags: Optional[list[str]] = None
    display_config: Optional[dict] = None


class DeviceCommand(BaseModel):
    """Schema for sending commands to devices."""

    command: str = Field(..., description="Command to send (refresh, reboot, etc.)")
    parameters: dict = Field(default_factory=dict)


class DeviceAuthRequest(BaseModel):
    """Schema for device authentication."""

    hardware_id: str = Field(..., description="Hardware ID of the device")
    device_secret: str = Field(..., description="Device secret for authentication")


class DeviceAuthResponse(BaseModel):
    """Response for successful device authentication."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    device_id: str
    organization_id: str


class HeartbeatRequest(BaseModel):
    """Schema for device heartbeat."""

    cpu_usage_percent: Optional[float] = None
    memory_usage_percent: Optional[float] = None
    storage_used_gb: Optional[float] = None
    temperature_celsius: Optional[int] = None
    bandwidth_mbps: Optional[int] = None
    latency_ms: Optional[int] = None
    current_playlist_id: Optional[str] = None
    current_asset_id: Optional[str] = None
    playback_position_sec: Optional[int] = None
    firmware_version: Optional[str] = None
    client_version: Optional[str] = None


class HeartbeatResponse(BaseModel):
    """Response for device heartbeat."""

    status: str
    message: str
    device_id: str


class DevicePlaylistItemResponse(BaseModel):
    """Single playlist item response for devices."""

    id: str
    asset_id: str
    position: int
    duration_seconds: int
    transition_override: Optional[str]
    custom_settings: dict
    # Include asset details for device download
    asset_file_path: str
    asset_file_size: int
    asset_mime_type: str


class DevicePlaylistResponse(BaseModel):
    """Device playlist response with all items."""

    id: str
    name: str
    description: Optional[str]
    loop_mode: bool
    shuffle: bool
    transition_type: str
    transition_duration_ms: int
    schedule_config: dict
    is_active: bool
    total_duration_sec: Optional[int]
    item_count: int
    items: list[DevicePlaylistItemResponse]


class AssignPlaylistRequest(BaseModel):
    """Schema for assigning a playlist to a device."""

    playlist_id: str


class AssignPlaylistResponse(BaseModel):
    """Response for assigning a playlist to a device."""

    message: str
    device_id: str
    playlist_id: str


# =============================================================================
# Endpoints
# =============================================================================
@router.get("", response_model=DeviceListResponse)
async def list_devices(
    current_user: CurrentUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
) -> DeviceListResponse:
    """
    List all devices for the organization.

    Supports pagination, search, and filtering by status.
    """
    org_id = current_user.organization_id
    offset = (page - 1) * limit

    # Build query
    query = select(Device).where(
        Device.organization_id == org_id,
        Device.deleted_at.is_(None),
    )

    # Apply filters
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Device.name.ilike(search_pattern),
                Device.hardware_id.ilike(search_pattern),
            )
        )

    if status:
        query = query.where(Device.status == status)

    # Get total count
    from sqlalchemy import func

    count_query = select(func.count()).select_from(query.alias())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.order_by(Device.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    devices = result.scalars().all()

    # Convert to response format
    items = [
        {
            "id": str(device.id),
            "name": device.name,
            "hardware_type": device.hardware_type,
            "hardware_id": device.hardware_id,
            "status": device.status,
            "last_heartbeat": device.last_heartbeat.isoformat() if device.last_heartbeat else None,
            "location_metadata": device.location_metadata,
            "tags": device.tags,
            "display_config": device.display_config,
            "network_info": device.network_info,
            "firmware_version": device.firmware_version,
            "client_version": device.client_version,
            "current_playlist_id": str(device.current_playlist_id) if device.current_playlist_id else None,
            "organization_id": str(device.organization_id),
            "created_at": device.created_at.isoformat() + "Z",
            "updated_at": device.updated_at.isoformat() + "Z",
        }
        for device in devices
    ]

    import math

    total_pages = max(1, math.ceil(total / limit)) if total > 0 else 1

    return DeviceListResponse(
        items=items,
        meta=PaginationMeta(
            total=total,
            page=page,
            page_size=limit,
            pages=total_pages,
        ),
    )


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    current_user: CurrentUser,
    db: DBSession,
) -> DeviceResponse:
    """Get a specific device by ID."""
    try:
        device_uuid = pyUUID(device_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid device ID")

    result = await db.execute(
        select(Device).where(
            Device.id == device_uuid,
            Device.organization_id == current_user.organization_id,
            Device.deleted_at.is_(None),
        )
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    return DeviceResponse(
        id=str(device.id),
        name=device.name,
        hardware_type=device.hardware_type,
        hardware_id=device.hardware_id,
        status=device.status,
        last_heartbeat=device.last_heartbeat.isoformat() if device.last_heartbeat else None,
        location_metadata=device.location_metadata,
        tags=device.tags,
        display_config=device.display_config,
        network_info=device.network_info,
        firmware_version=device.firmware_version,
        client_version=device.client_version,
        current_playlist_id=str(device.current_playlist_id) if device.current_playlist_id else None,
        organization_id=str(device.organization_id),
        created_at=device.created_at.isoformat() + "Z",
        updated_at=device.updated_at.isoformat() + "Z",
    )


@router.post("", response_model=DeviceRegistrationResponse, status_code=201)
async def create_device(
    data: DeviceCreate,
    current_user: CurrentUser,
    db: DBSession,
) -> DeviceRegistrationResponse:
    """Register a new device."""
    # Check if hardware_id already exists
    existing = await db.execute(
        select(Device).where(
            Device.hardware_id == data.hardware_id,
            Device.deleted_at.is_(None),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Hardware ID already registered")

    # Generate a device secret for authentication
    device_secret = secrets.token_urlsafe(32)
    device_secret_hash = hash_device_secret(device_secret)

    device = Device(
        name=data.name,
        hardware_type=data.hardware_type,
        hardware_id=data.hardware_id,
        device_secret_hash=device_secret_hash,
        status=DeviceStatus.PENDING,
        location_metadata=data.location_metadata,
        tags=data.tags,
        display_config={},
        organization_id=current_user.organization_id,
    )

    db.add(device)
    await db.commit()
    await db.refresh(device)

    device_response = DeviceResponse(
        id=str(device.id),
        name=device.name,
        hardware_type=device.hardware_type,
        hardware_id=device.hardware_id,
        status=device.status,
        last_heartbeat=device.last_heartbeat.isoformat() if device.last_heartbeat else None,
        location_metadata=device.location_metadata,
        tags=device.tags,
        display_config=device.display_config,
        network_info=device.network_info,
        firmware_version=device.firmware_version,
        client_version=device.client_version,
        current_playlist_id=str(device.current_playlist_id) if device.current_playlist_id else None,
        organization_id=str(device.organization_id),
        created_at=device.created_at.isoformat() + "Z",
        updated_at=device.updated_at.isoformat() + "Z",
    )

    return DeviceRegistrationResponse(
        device=device_response,
        device_secret=device_secret,
    )


@router.patch("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: str,
    data: DeviceUpdate,
    current_user: CurrentUser,
    db: DBSession,
) -> DeviceResponse:
    """Update an existing device."""
    try:
        device_uuid = pyUUID(device_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid device ID")

    result = await db.execute(
        select(Device).where(
            Device.id == device_uuid,
            Device.organization_id == current_user.organization_id,
            Device.deleted_at.is_(None),
        )
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Update fields
    if data.name is not None:
        device.name = data.name
    if data.status is not None:
        device.status = data.status
    if data.location_metadata is not None:
        device.location_metadata = data.location_metadata
    if data.tags is not None:
        device.tags = data.tags
    if data.display_config is not None:
        device.display_config = data.display_config

    await db.commit()
    await db.refresh(device)

    return DeviceResponse(
        id=str(device.id),
        name=device.name,
        hardware_type=device.hardware_type,
        hardware_id=device.hardware_id,
        status=device.status,
        last_heartbeat=device.last_heartbeat.isoformat() if device.last_heartbeat else None,
        location_metadata=device.location_metadata,
        tags=device.tags,
        display_config=device.display_config,
        network_info=device.network_info,
        firmware_version=device.firmware_version,
        client_version=device.client_version,
        current_playlist_id=str(device.current_playlist_id) if device.current_playlist_id else None,
        organization_id=str(device.organization_id),
        created_at=device.created_at.isoformat() + "Z",
        updated_at=device.updated_at.isoformat() + "Z",
    )


@router.delete("/{device_id}", status_code=204)
async def delete_device(
    device_id: str,
    current_user: CurrentUser,
    db: DBSession,
) -> None:
    """Delete a device (soft delete)."""
    try:
        device_uuid = pyUUID(device_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid device ID")

    result = await db.execute(
        select(Device).where(
            Device.id == device_uuid,
            Device.organization_id == current_user.organization_id,
            Device.deleted_at.is_(None),
        )
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Soft delete
    device.soft_delete()
    await db.commit()


@router.post("/{device_id}/regenerate-secret", response_model=DeviceRegistrationResponse)
async def regenerate_device_secret(
    device_id: str,
    current_user: CurrentUser,
    db: DBSession,
) -> DeviceRegistrationResponse:
    """
    Regenerate a device's secret.

    Returns the new device secret. This is the only time the secret will be shown.
    Save it securely - it cannot be retrieved again.
    """
    try:
        device_uuid = pyUUID(device_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid device ID")

    result = await db.execute(
        select(Device).where(
            Device.id == device_uuid,
            Device.organization_id == current_user.organization_id,
            Device.deleted_at.is_(None),
        )
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Generate a new device secret
    device_secret = secrets.token_urlsafe(32)
    device.device_secret_hash = hash_device_secret(device_secret)

    await db.commit()
    await db.refresh(device)

    device_response = DeviceResponse(
        id=str(device.id),
        name=device.name,
        hardware_type=device.hardware_type,
        hardware_id=device.hardware_id,
        status=device.status,
        last_heartbeat=device.last_heartbeat.isoformat() if device.last_heartbeat else None,
        location_metadata=device.location_metadata,
        tags=device.tags,
        display_config=device.display_config,
        network_info=device.network_info,
        firmware_version=device.firmware_version,
        client_version=device.client_version,
        current_playlist_id=str(device.current_playlist_id) if device.current_playlist_id else None,
        organization_id=str(device.organization_id),
        created_at=device.created_at.isoformat() + "Z",
        updated_at=device.updated_at.isoformat() + "Z",
    )

    return DeviceRegistrationResponse(
        device=device_response,
        device_secret=device_secret,
    )


@router.post("/{device_id}/command", response_model=dict)
async def send_device_command(
    device_id: str,
    command: DeviceCommand,
    current_user: CurrentUser,
    db: DBSession,
) -> dict:
    """
    Send a command to a device.

    In production, this would use Redis pub/sub to send commands
    to connected devices. For now, we'll just update the device status.
    """
    try:
        device_uuid = pyUUID(device_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid device ID")

    result = await db.execute(
        select(Device).where(
            Device.id == device_uuid,
            Device.organization_id == current_user.organization_id,
            Device.deleted_at.is_(None),
        )
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # In production, this would publish to Redis
    # For now, just acknowledge the command
    return {
        "message": "Command sent to device",
        "device_id": str(device.id),
        "command": command.command,
        "timestamp": datetime.now().isoformat(),
    }


# =============================================================================
# Device Connection Endpoints
# =============================================================================
@router.post("/auth", response_model=DeviceAuthResponse)
async def authenticate_device(
    data: DeviceAuthRequest,
    db: DBSession,
) -> DeviceAuthResponse:
    """
    Authenticate a device using its hardware_id and device_secret.

    Returns a JWT token that the device should use for subsequent requests.
    """
    # Find device by hardware_id
    result = await db.execute(
        select(Device).where(
            Device.hardware_id == data.hardware_id,
            Device.deleted_at.is_(None),
        )
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Verify device secret
    if not verify_device_secret(data.device_secret, device.device_secret_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create device token (valid for 30 days)
    from app.core.config import get_settings

    settings = get_settings()
    access_token = create_device_token(
        device_id=str(device.id),
        org_id=str(device.organization_id),
        expires_delta=None,  # Use default from settings
    )

    return DeviceAuthResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.device_token_expire_days * 24 * 60 * 60,
        device_id=str(device.id),
        organization_id=str(device.organization_id),
    )


@router.post("/{device_id}/heartbeat", response_model=HeartbeatResponse)
async def device_heartbeat(
    device_id: str,
    data: HeartbeatRequest,
    db: DBSession,
) -> HeartbeatResponse:
    """
    Receive heartbeat from a device.

    Updates device status, last heartbeat time, and stores health metrics.
    Transitions device from PENDING to ACTIVE on first heartbeat.
    """
    try:
        device_uuid = pyUUID(device_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid device ID")

    result = await db.execute(
        select(Device).where(
            Device.id == device_uuid,
            Device.deleted_at.is_(None),
        )
    )
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Update device heartbeat using the model method
    device.update_heartbeat(
        cpu_percent=data.cpu_usage_percent,
        memory_percent=data.memory_usage_percent,
        storage_used=data.storage_used_gb,
        temperature=data.temperature_celsius,
        bandwidth_mbps=data.bandwidth_mbps,
        latency_ms=data.latency_ms,
        current_playlist=pyUUID(data.current_playlist_id) if data.current_playlist_id else None,
        current_asset=pyUUID(data.current_asset_id) if data.current_asset_id else None,
        playback_position=data.playback_position_sec,
    )

    # Update firmware/client versions if provided
    if data.firmware_version:
        device.firmware_version = data.firmware_version
    if data.client_version:
        device.client_version = data.client_version

    await db.commit()

    # Store detailed heartbeat metrics in DeviceHeartbeat table (for time-series data)
    # This would use TimescaleDB in production
    # TODO: Implement DeviceHeartbeat model insertion

    status_message = "Device is active"
    if device.status == DeviceStatus.ACTIVE:
        status_message = "Heartbeat received, device is active"
    elif device.status == DeviceStatus.PENDING:
        status_message = "Device activated successfully"

    return HeartbeatResponse(
        status=device.status,
        message=status_message,
        device_id=str(device.id),
    )


# =============================================================================
# Device Playlist Endpoints
# =============================================================================
@router.get("/{device_id}/playlists", response_model=DevicePlaylistResponse)
async def get_device_playlist(
    device_id: str,
    current_user: CurrentUser,
    db: DBSession,
) -> DevicePlaylistResponse:
    """
    Get the currently assigned playlist for a device.

    Returns the playlist with all items and asset details needed
    for the device to download and display content.
    """
    try:
        device_uuid = pyUUID(device_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid device ID")

    # Get device
    device_result = await db.execute(
        select(Device).where(
            Device.id == device_uuid,
            Device.organization_id == current_user.organization_id,
            Device.deleted_at.is_(None),
        )
    )
    device = device_result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Check if device has a playlist assigned
    if not device.current_playlist_id:
        raise HTTPException(status_code=404, detail="No playlist assigned to device")

    # Get playlist
    playlist_result = await db.execute(
        select(Playlist).where(
            Playlist.id == device.current_playlist_id,
            Playlist.organization_id == current_user.organization_id,
            Playlist.deleted_at.is_(None),
        )
    )
    playlist = playlist_result.scalar_one_or_none()

    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    # Get playlist items with asset details
    items_result = await db.execute(
        select(PlaylistItem, Asset)
        .join(Asset, PlaylistItem.asset_id == Asset.id)
        .where(PlaylistItem.playlist_id == playlist.id)
        .order_by(PlaylistItem.position)
    )
    items_assets = items_result.all()

    items = [
        DevicePlaylistItemResponse(
            id=str(item.id),
            asset_id=str(item.asset_id),
            position=item.position,
            duration_seconds=item.duration_seconds,
            transition_override=item.transition_override,
            custom_settings=item.custom_settings,
            asset_file_path=asset.file_path,
            asset_file_size=asset.file_size,
            asset_mime_type=f"model/{asset.file_format}",
        )
        for item, asset in items_assets
    ]

    return DevicePlaylistResponse(
        id=str(playlist.id),
        name=playlist.name,
        description=playlist.description,
        loop_mode=playlist.loop_mode,
        shuffle=playlist.shuffle,
        transition_type=playlist.transition_type,
        transition_duration_ms=playlist.transition_duration_ms,
        schedule_config=playlist.schedule_config,
        is_active=playlist.is_active,
        total_duration_sec=playlist.total_duration_sec,
        item_count=playlist.item_count,
        items=items,
    )


@router.post("/{device_id}/playlists", response_model=AssignPlaylistResponse, status_code=200)
async def assign_playlist_to_device(
    device_id: str,
    data: AssignPlaylistRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> AssignPlaylistResponse:
    """
    Assign a playlist to a device.

    Sets the device's current_playlist_id and creates a DevicePlaylist
    association record for tracking.
    """
    try:
        device_uuid = pyUUID(device_id)
        playlist_uuid = pyUUID(data.playlist_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid device ID or playlist ID")

    # Get device
    device_result = await db.execute(
        select(Device).where(
            Device.id == device_uuid,
            Device.organization_id == current_user.organization_id,
            Device.deleted_at.is_(None),
        )
    )
    device = device_result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Get playlist
    playlist_result = await db.execute(
        select(Playlist).where(
            Playlist.id == playlist_uuid,
            Playlist.organization_id == current_user.organization_id,
            Playlist.deleted_at.is_(None),
        )
    )
    playlist = playlist_result.scalar_one_or_none()

    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    # Check if playlist has items
    if playlist.item_count == 0:
        raise HTTPException(status_code=400, detail="Cannot assign empty playlist to device")

    # Update device's current playlist
    device.current_playlist_id = playlist_uuid

    # Create DevicePlaylist association if it doesn't exist
    from app.models.playlist import DevicePlaylist

    existing_dp = await db.execute(
        select(DevicePlaylist).where(
            DevicePlaylist.device_id == device_uuid,
            DevicePlaylist.playlist_id == playlist_uuid,
        )
    )
    if not existing_dp.scalar_one_or_none():
        device_playlist = DevicePlaylist(
            device_id=device_uuid,
            playlist_id=playlist_uuid,
            assigned_by=current_user.id,
        )
        db.add(device_playlist)

    await db.commit()

    return AssignPlaylistResponse(
        message="Playlist assigned to device successfully",
        device_id=str(device.id),
        playlist_id=str(playlist.id),
    )
