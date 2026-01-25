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
from app.models import Device, DeviceStatus
from app.core.security import hash_device_secret, generate_activation_code
from uuid_utils import uuid4
from uuid_utils.compat import UUID as pyUUID
import secrets


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


@router.post("", response_model=DeviceResponse, status_code=201)
async def create_device(
    data: DeviceCreate,
    current_user: CurrentUser,
    db: DBSession,
) -> DeviceResponse:
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

    device = Device(
        name=data.name,
        hardware_type=data.hardware_type,
        hardware_id=data.hardware_id,
        status=DeviceStatus.PENDING,
        location_metadata=data.location_metadata,
        tags=data.tags,
        organization_id=current_user.organization_id,
    )

    db.add(device)
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
