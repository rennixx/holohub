"""
Assets API

Endpoints for managing holographic assets.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DBSession
from app.models import Asset, AssetStatus
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


class AssetListResponse(BaseModel):
    """Paginated list of assets."""

    items: list[dict]
    meta: PaginationMeta


class AssetResponse(BaseModel):
    """Single asset response."""

    id: str
    name: str
    description: Optional[str]
    file_path: str
    file_size: int
    file_format: str
    status: str
    thumbnail_url: Optional[str]
    metadata: dict
    created_by_id: Optional[str]
    organization_id: str
    created_at: str
    updated_at: str


class AssetCreate(BaseModel):
    """Schema for creating an asset."""

    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    file_path: str = Field(..., max_length=500)
    file_size: int = Field(..., ge=0)
    file_format: str = Field(..., max_length=50)


class AssetUpdate(BaseModel):
    """Schema for updating an asset."""

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None
    thumbnail_url: Optional[str] = None
    metadata: Optional[dict] = None


# =============================================================================
# Endpoints
# =============================================================================
@router.get("", response_model=AssetListResponse)
async def list_assets(
    current_user: CurrentUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
) -> AssetListResponse:
    """
    List all assets for the organization.

    Supports pagination, search, and filtering by status.
    """
    org_id = current_user.organization_id
    offset = (page - 1) * limit

    # Build query
    query = select(Asset).where(
        Asset.organization_id == org_id,
        Asset.deleted_at.is_(None),
    )

    # Apply filters
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            or_(
                Asset.name.ilike(search_pattern),
                Asset.description.ilike(search_pattern),
            )
        )

    if status:
        query = query.where(Asset.status == status)

    # Get total count
    from sqlalchemy import func

    count_query = select(func.count()).select_from(query.alias())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.order_by(Asset.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    assets = result.scalars().all()

    # Convert to response format
    items = [
        {
            "id": str(asset.id),
            "name": asset.name,
            "description": asset.description,
            "file_path": asset.file_path,
            "file_size": asset.file_size,
            "file_format": asset.file_format,
            "status": asset.status,
            "thumbnail_url": asset.thumbnail_url,
            "metadata": asset.asset_metadata,
            "created_by_id": str(asset.created_by_id) if asset.created_by_id else None,
            "organization_id": str(asset.organization_id),
            "created_at": asset.created_at.isoformat(),
            "updated_at": asset.updated_at.isoformat(),
        }
        for asset in assets
    ]

    import math

    total_pages = max(1, math.ceil(total / limit)) if total > 0 else 1

    return AssetListResponse(
        items=items,
        meta=PaginationMeta(
            total=total,
            page=page,
            page_size=limit,
            pages=total_pages,
        ),
    )


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: str,
    current_user: CurrentUser,
    db: DBSession,
) -> AssetResponse:
    """
    Get a specific asset by ID.
    """
    try:
        asset_uuid = pyUUID(asset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset ID")

    result = await db.execute(
        select(Asset).where(
            Asset.id == asset_uuid,
            Asset.organization_id == current_user.organization_id,
            Asset.deleted_at.is_(None),
        )
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    return AssetResponse(
        id=str(asset.id),
        name=asset.name,
        description=asset.description,
        file_path=asset.file_path,
        file_size=asset.file_size,
        file_format=asset.file_format,
        status=asset.status,
        thumbnail_url=asset.thumbnail_url,
        metadata=asset.asset_metadata,
        created_by_id=str(asset.created_by_id) if asset.created_by_id else None,
        organization_id=str(asset.organization_id),
        created_at=asset.created_at.isoformat(),
        updated_at=asset.updated_at.isoformat(),
    )


@router.post("", response_model=AssetResponse, status_code=201)
async def create_asset(
    data: AssetCreate,
    current_user: CurrentUser,
    db: DBSession,
) -> AssetResponse:
    """
    Create a new asset.

    Note: This is a simplified version. In production, you'd upload
    files to S3/MinIO first, then create the asset record.
    """
    asset = Asset(
        name=data.name,
        description=data.description,
        file_path=data.file_path,
        file_size=data.file_size,
        file_format=data.file_format,
        status=AssetStatus.UPLOADING,
        created_by_id=current_user.id,
        organization_id=current_user.organization_id,
    )

    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    return AssetResponse(
        id=str(asset.id),
        name=asset.name,
        description=asset.description,
        file_path=asset.file_path,
        file_size=asset.file_size,
        file_format=asset.file_format,
        status=asset.status,
        thumbnail_url=asset.thumbnail_url,
        metadata=asset.asset_metadata,
        created_by_id=str(asset.created_by_id) if asset.created_by_id else None,
        organization_id=str(asset.organization_id),
        created_at=asset.created_at.isoformat(),
        updated_at=asset.updated_at.isoformat(),
    )


@router.patch("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: str,
    data: AssetUpdate,
    current_user: CurrentUser,
    db: DBSession,
) -> AssetResponse:
    """
    Update an existing asset.
    """
    try:
        asset_uuid = pyUUID(asset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset ID")

    result = await db.execute(
        select(Asset).where(
            Asset.id == asset_uuid,
            Asset.organization_id == current_user.organization_id,
            Asset.deleted_at.is_(None),
        )
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Update fields
    if data.name is not None:
        asset.name = data.name
    if data.description is not None:
        asset.description = data.description
    if data.status is not None:
        asset.status = data.status
    if data.thumbnail_url is not None:
        asset.thumbnail_url = data.thumbnail_url
    if data.metadata is not None:
        asset.asset_metadata = data.metadata

    await db.commit()
    await db.refresh(asset)

    return AssetResponse(
        id=str(asset.id),
        name=asset.name,
        description=asset.description,
        file_path=asset.file_path,
        file_size=asset.file_size,
        file_format=asset.file_format,
        status=asset.status,
        thumbnail_url=asset.thumbnail_url,
        metadata=asset.asset_metadata,
        created_by_id=str(asset.created_by_id) if asset.created_by_id else None,
        organization_id=str(asset.organization_id),
        created_at=asset.created_at.isoformat(),
        updated_at=asset.updated_at.isoformat(),
    )


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(
    asset_id: str,
    current_user: CurrentUser,
    db: DBSession,
) -> None:
    """
    Delete an asset (soft delete).
    """
    try:
        asset_uuid = pyUUID(asset_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid asset ID")

    result = await db.execute(
        select(Asset).where(
            Asset.id == asset_uuid,
            Asset.organization_id == current_user.organization_id,
            Asset.deleted_at.is_(None),
        )
    )
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Soft delete
    asset.soft_delete()
    await db.commit()
