"""
Playlists API

Endpoints for managing playlists and content scheduling.
"""
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, or_

from app.api.deps import CurrentUser, DBSession
from app.models import Playlist, PlaylistItem, TransitionType
from uuid_utils import uuid4
from uuid_utils.compat import UUID as pyUUID


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


class PlaylistListResponse(BaseModel):
    """Paginated list of playlists."""

    items: list[dict]
    meta: PaginationMeta


class PlaylistResponse(BaseModel):
    """Single playlist response."""

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
    created_by: Optional[str]
    organization_id: str
    created_at: str
    updated_at: str


class PlaylistCreate(BaseModel):
    """Schema for creating a playlist."""

    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    loop_mode: bool = True
    shuffle: bool = False
    transition_type: str = TransitionType.FADE
    transition_duration_ms: int = 500
    schedule_config: dict = Field(default_factory=dict)


class PlaylistUpdate(BaseModel):
    """Schema for updating a playlist."""

    name: Optional[str] = None
    description: Optional[str] = None
    loop_mode: Optional[bool] = None
    shuffle: Optional[bool] = None
    transition_type: Optional[str] = None
    transition_duration_ms: Optional[int] = None
    schedule_config: Optional[dict] = None
    is_active: Optional[bool] = None


class PlaylistItemCreate(BaseModel):
    """Schema for adding an item to a playlist."""

    asset_id: str
    position: Optional[int] = None
    duration_seconds: int = 10
    transition_override: Optional[str] = None


class PlaylistItemResponse(BaseModel):
    """Single playlist item response."""

    id: str
    playlist_id: str
    asset_id: str
    position: int
    duration_seconds: int
    transition_override: Optional[str]
    custom_settings: dict
    created_at: str


# =============================================================================
# Endpoints
# =============================================================================
@router.get("", response_model=PlaylistListResponse)
async def list_playlists(
    current_user: CurrentUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
) -> PlaylistListResponse:
    """List all playlists for the organization."""
    org_id = current_user.organization_id
    offset = (page - 1) * limit

    # Build query
    query = select(Playlist).where(
        Playlist.organization_id == org_id,
        Playlist.deleted_at.is_(None),
    )

    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Playlist.name.ilike(search_pattern),
                Playlist.description.ilike(search_pattern),
            )
        )

    # Get total count
    from sqlalchemy import func

    count_query = select(func.count()).select_from(query.alias())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.order_by(Playlist.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    playlists = result.scalars().all()

    # Convert to response format
    items = [
        {
            "id": str(playlist.id),
            "name": playlist.name,
            "description": playlist.description,
            "loop_mode": playlist.loop_mode,
            "shuffle": playlist.shuffle,
            "transition_type": playlist.transition_type,
            "transition_duration_ms": playlist.transition_duration_ms,
            "schedule_config": playlist.schedule_config,
            "is_active": playlist.is_active,
            "total_duration_sec": playlist.total_duration_sec,
            "item_count": playlist.item_count,
            "created_by": str(playlist.created_by) if playlist.created_by else None,
            "organization_id": str(playlist.organization_id),
            "created_at": playlist.created_at.isoformat(),
            "updated_at": playlist.updated_at.isoformat(),
        }
        for playlist in playlists
    ]

    import math

    total_pages = max(1, math.ceil(total / limit)) if total > 0 else 1

    return PlaylistListResponse(
        items=items,
        meta=PaginationMeta(
            total=total,
            page=page,
            page_size=limit,
            pages=total_pages,
        ),
    )


@router.get("/{playlist_id}", response_model=PlaylistResponse)
async def get_playlist(
    playlist_id: str,
    current_user: CurrentUser,
    db: DBSession,
) -> PlaylistResponse:
    """Get a specific playlist by ID."""
    try:
        playlist_uuid = pyUUID(playlist_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid playlist ID")

    result = await db.execute(
        select(Playlist).where(
            Playlist.id == playlist_uuid,
            Playlist.organization_id == current_user.organization_id,
            Playlist.deleted_at.is_(None),
        )
    )
    playlist = result.scalar_one_or_none()

    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    return PlaylistResponse(
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
        created_by=str(playlist.created_by) if playlist.created_by else None,
        organization_id=str(playlist.organization_id),
        created_at=playlist.created_at.isoformat(),
        updated_at=playlist.updated_at.isoformat(),
    )


@router.get("/{playlist_id}/items", response_model=list[PlaylistItemResponse])
async def get_playlist_items(
    playlist_id: str,
    current_user: CurrentUser,
    db: DBSession,
) -> list[PlaylistItemResponse]:
    """Get all items in a playlist."""
    try:
        playlist_uuid = pyUUID(playlist_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid playlist ID")

    # Verify playlist exists and belongs to org
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

    # Get items
    result = await db.execute(
        select(PlaylistItem)
        .where(PlaylistItem.playlist_id == playlist_uuid)
        .order_by(PlaylistItem.position)
    )
    items = result.scalars().all()

    return [
        PlaylistItemResponse(
            id=str(item.id),
            playlist_id=str(item.playlist_id),
            asset_id=str(item.asset_id),
            position=item.position,
            duration_seconds=item.duration_seconds,
            transition_override=item.transition_override,
            custom_settings=item.custom_settings,
            created_at=item.created_at.isoformat(),
        )
        for item in items
    ]


@router.post("", response_model=PlaylistResponse, status_code=201)
async def create_playlist(
    data: PlaylistCreate,
    current_user: CurrentUser,
    db: DBSession,
) -> PlaylistResponse:
    """Create a new playlist."""
    playlist = Playlist(
        name=data.name,
        description=data.description,
        loop_mode=data.loop_mode,
        shuffle=data.shuffle,
        transition_type=data.transition_type,
        transition_duration_ms=data.transition_duration_ms,
        schedule_config=data.schedule_config,
        is_active=True,
        item_count=0,
        created_by=current_user.id,
        organization_id=current_user.organization_id,
    )

    db.add(playlist)
    await db.commit()
    await db.refresh(playlist)

    return PlaylistResponse(
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
        created_by=str(playlist.created_by) if playlist.created_by else None,
        organization_id=str(playlist.organization_id),
        created_at=playlist.created_at.isoformat(),
        updated_at=playlist.updated_at.isoformat(),
    )


@router.post("/{playlist_id}/items", response_model=PlaylistItemResponse, status_code=201)
async def add_playlist_item(
    playlist_id: str,
    data: PlaylistItemCreate,
    current_user: CurrentUser,
    db: DBSession,
) -> PlaylistItemResponse:
    """Add an asset to a playlist."""
    try:
        playlist_uuid = pyUUID(playlist_id)
        asset_uuid = pyUUID(data.asset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid playlist ID or asset ID")

    # Verify playlist exists
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

    # Get position
    position = data.position if data.position is not None else playlist.item_count

    # Create item
    item = PlaylistItem(
        playlist_id=playlist_uuid,
        asset_id=asset_uuid,
        position=position,
        duration_seconds=data.duration_seconds,
        transition_override=data.transition_override,
    )

    db.add(item)

    # Update playlist count
    playlist.item_count += 1

    await db.commit()
    await db.refresh(item)

    return PlaylistItemResponse(
        id=str(item.id),
        playlist_id=str(item.playlist_id),
        asset_id=str(item.asset_id),
        position=item.position,
        duration_seconds=item.duration_seconds,
        transition_override=item.transition_override,
        custom_settings=item.custom_settings,
        created_at=item.created_at.isoformat(),
    )


@router.patch("/{playlist_id}", response_model=PlaylistResponse)
async def update_playlist(
    playlist_id: str,
    data: PlaylistUpdate,
    current_user: CurrentUser,
    db: DBSession,
) -> PlaylistResponse:
    """Update an existing playlist."""
    try:
        playlist_uuid = pyUUID(playlist_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid playlist ID")

    result = await db.execute(
        select(Playlist).where(
            Playlist.id == playlist_uuid,
            Playlist.organization_id == current_user.organization_id,
            Playlist.deleted_at.is_(None),
        )
    )
    playlist = result.scalar_one_or_none()

    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    # Update fields
    if data.name is not None:
        playlist.name = data.name
    if data.description is not None:
        playlist.description = data.description
    if data.loop_mode is not None:
        playlist.loop_mode = data.loop_mode
    if data.shuffle is not None:
        playlist.shuffle = data.shuffle
    if data.transition_type is not None:
        playlist.transition_type = data.transition_type
    if data.transition_duration_ms is not None:
        playlist.transition_duration_ms = data.transition_duration_ms
    if data.schedule_config is not None:
        playlist.schedule_config = data.schedule_config
    if data.is_active is not None:
        playlist.is_active = data.is_active

    await db.commit()
    await db.refresh(playlist)

    return PlaylistResponse(
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
        created_by=str(playlist.created_by) if playlist.created_by else None,
        organization_id=str(playlist.organization_id),
        created_at=playlist.created_at.isoformat(),
        updated_at=playlist.updated_at.isoformat(),
    )


@router.delete("/{playlist_id}", status_code=204)
async def delete_playlist(
    playlist_id: str,
    current_user: CurrentUser,
    db: DBSession,
) -> None:
    """Delete a playlist (soft delete)."""
    try:
        playlist_uuid = pyUUID(playlist_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid playlist ID")

    result = await db.execute(
        select(Playlist).where(
            Playlist.id == playlist_uuid,
            Playlist.organization_id == current_user.organization_id,
            Playlist.deleted_at.is_(None),
        )
    )
    playlist = result.scalar_one_or_none()

    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    # Soft delete
    playlist.soft_delete()
    await db.commit()


@router.delete("/{playlist_id}/items/{item_id}", status_code=204)
async def remove_playlist_item(
    playlist_id: str,
    item_id: str,
    current_user: CurrentUser,
    db: DBSession,
) -> None:
    """Remove an item from a playlist."""
    try:
        playlist_uuid = pyUUID(playlist_id)
        item_uuid = pyUUID(item_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid playlist ID or item ID")

    # Verify playlist exists
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

    # Get and delete item
    result = await db.execute(
        select(PlaylistItem).where(
            PlaylistItem.id == item_uuid,
            PlaylistItem.playlist_id == playlist_uuid,
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Playlist item not found")

    # Delete item
    await db.delete(item)

    # Update playlist count and reorder
    playlist.item_count -= 1

    # Reorder remaining items
    items_result = await db.execute(
        select(PlaylistItem)
        .where(PlaylistItem.playlist_id == playlist_uuid)
        .order_by(PlaylistItem.position)
    )
    for i, remaining in enumerate(items_result.scalars()):
        if remaining.position > item.position:
            remaining.position = i

    await db.commit()
