"""
Assets API

Endpoints for managing holographic assets.
"""
from datetime import timedelta
from typing import Optional
from uuid import UUID
import os
import io

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File as FastAPIFile
from pydantic import BaseModel, Field
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
import boto3
from botocore.config import Config

from app.api.deps import CurrentUser, DBSession
from app.core.config import get_settings
from app.models import Asset, AssetStatus
from uuid_utils import uuid4
from uuid_utils.compat import UUID as pyUUID


settings = get_settings()


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


class UploadRequestRequest(BaseModel):
    """Schema for requesting an upload URL."""

    filename: str = Field(..., max_length=255)
    file_size: int = Field(..., ge=1, description="File size in bytes")
    mime_type: str = Field(..., max_length=100)


class UploadRequestResponse(BaseModel):
    """Response with upload URL and asset ID."""

    id: str
    upload_url: str
    file_path: str


class UploadConfirmRequest(BaseModel):
    """Schema for confirming an upload."""

    upload_id: str
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)


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


# =============================================================================
# Upload Endpoints
# =============================================================================
def _get_s3_client():
    """Get S3 client for MinIO operations."""
    s3_config = Config(
        region_name=settings.s3_region,
        signature_version="s3v4",
    )
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        config=s3_config,
    )


@router.post("/upload/request", response_model=UploadRequestResponse)
async def request_upload_url(
    data: UploadRequestRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> UploadRequestResponse:
    """
    Request a presigned upload URL for a new asset.

    Returns an upload ID and a presigned URL that can be used to upload
    the file directly to MinIO/S3.
    """
    # Validate file extension
    file_ext = os.path.splitext(data.filename)[1].lower()
    if file_ext not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(settings.allowed_extensions_list)}",
        )

    # Validate file size
    max_size = settings.max_upload_size_mb * 1024 * 1024
    if data.file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.max_upload_size_mb}MB",
        )

    # Generate unique file path
    asset_id = uuid4()
    file_path = f"assets/{current_user.organization_id}/{asset_id}/{data.filename}"

    # Create presigned URL for upload
    s3_client = _get_s3_client()
    try:
        upload_url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.s3_bucket,
                "Key": file_path,
                "ContentType": data.mime_type,
            },
            ExpiresIn=3600,  # 1 hour
        )
        # Replace internal hostname with public endpoint for frontend access
        # In development, minio:9000 -> localhost:9000
        upload_url = upload_url.replace("minio:9000", "localhost:9000")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate upload URL: {str(e)}")

    return UploadRequestResponse(
        id=str(asset_id),
        upload_url=upload_url,
        file_path=file_path,
    )


@router.post("/upload/confirm", response_model=AssetResponse)
async def confirm_upload(
    data: UploadConfirmRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> AssetResponse:
    """
    Confirm an upload and create the asset record.

    After uploading the file to MinIO/S3 using the presigned URL,
    call this endpoint to create the asset record in the database.
    """
    try:
        asset_id = pyUUID(data.upload_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid upload ID")

    # Verify the file exists in MinIO
    s3_client = _get_s3_client()
    file_path = f"assets/{current_user.organization_id}/{asset_id}/"

    try:
        # List objects with the prefix to find the uploaded file
        response = s3_client.list_objects_v2(
            Bucket=settings.s3_bucket,
            Prefix=file_path,
            MaxKeys=1,
        )

        if "Contents" not in response or not response["Contents"]:
            raise HTTPException(status_code=404, detail="File not found in storage")

        s3_object = response["Contents"][0]
        actual_file_path = s3_object["Key"]
        file_size = s3_object["Size"]

        # Extract file format from filename
        filename = actual_file_path.split("/")[-1]
        file_format = os.path.splitext(filename)[1].lstrip(".")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Failed to verify file: {str(e)}")

    # Get file format from path
    file_ext = os.path.splitext(filename)[1].lower()
    file_format = file_ext.lstrip(".")

    # Create asset record
    asset = Asset(
        id=asset_id,
        name=data.title,
        description=data.description,
        file_path=actual_file_path,
        file_size=file_size,
        file_format=file_format,
        status=AssetStatus.PROCESSING,
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
