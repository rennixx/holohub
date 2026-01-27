"""
Asset Schemas

Pydantic schemas for asset validation and serialization.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from uuid_utils.compat import UUID as pyUUID


# =============================================================================
# Base Schemas
# =============================================================================
class AssetBase(BaseModel):
    """Base asset schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    category: Optional[str] = Field(
        None,
        pattern="^(products|logos|characters|environments|animations|other)$",
    )
    custom_metadata: dict = Field(default_factory=dict)


# =============================================================================
# Create Schemas
# =============================================================================
class AssetCreate(AssetBase):
    """Schema for creating a new asset (metadata only)."""

    pass  # File upload is handled separately


# =============================================================================
# Update Schemas
# =============================================================================
class AssetUpdate(BaseModel):
    """Schema for updating asset metadata."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    category: Optional[str] = None
    custom_metadata: Optional[dict] = None
    visibility: Optional[str] = Field(None, pattern="^(private|shared|public)$")


# =============================================================================
# Upload/Processing Schemas
# =============================================================================
class AssetUploadResponse(BaseModel):
    """Response schema for asset upload."""

    asset_id: pyUUID
    processing_status: str
    upload_size_bytes: int
    estimated_processing_time_sec: Optional[int] = None


class AssetProcessRequest(BaseModel):
    """Schema for requesting asset reprocessing."""

    pipeline: str = Field(default="full", pattern="^(full|quilts_only|video_only|thumbnail_only)$")
    settings: dict = Field(default_factory=dict)
    # Example settings:
    # {
    #   "target_poly_count": 30000,
    #   "compression_level": 9,
    #   "quilt_formats": ["portrait_8x6", "landscape_5x9"]
    # }


class AssetProcessingStatus(BaseModel):
    """Schema for asset processing status."""

    asset_id: pyUUID
    status: str
    progress: float = Field(..., ge=0, le=100)
    current_step: Optional[str] = None
    error: Optional[str] = None
    logs: list[dict] = Field(default_factory=list)


# =============================================================================
# Response Schemas
# =============================================================================
class GeometryStats(BaseModel):
    """3D geometry statistics."""

    poly_count: Optional[int] = None
    vertex_count: Optional[int] = None
    triangle_count: Optional[int] = None
    material_count: Optional[int] = None
    texture_count: Optional[int] = None
    has_animations: Optional[bool] = None
    animation_duration_sec: Optional[float] = None
    bounding_box: Optional[dict] = None


class AssetOutput(BaseModel):
    """Asset processing output."""

    url: str
    size_bytes: int
    poly_count: Optional[int] = None
    compression_ratio: Optional[float] = None


class QuiltOutput(BaseModel):
    """Quilt output."""

    format: str
    url: str
    width: int
    height: int


class AssetOutputs(BaseModel):
    """All processed asset outputs."""

    optimized_glb: Optional[AssetOutput] = None
    draco_compressed: Optional[AssetOutput] = None
    quilts: list[QuiltOutput] = Field(default_factory=list)
    turntable_video: Optional[AssetOutput] = None
    thumbnail: Optional[AssetOutput] = None


class AssetResponse(AssetBase):
    """Schema for asset response."""

    model_config = ConfigDict(from_attributes=True)

    id: pyUUID
    organization_id: pyUUID
    original_filename: Optional[str]
    original_url: str
    file_size_bytes: Optional[int]
    mime_type: Optional[str]
    processing_status: str
    processing_started_at: Optional[datetime]
    processing_completed_at: Optional[datetime]
    processing_error: Optional[str]
    geometry_stats: GeometryStats
    outputs: AssetOutputs
    cdn_urls: AssetOutputs
    visibility: str
    view_count: int
    download_count: int
    device_usage_count: int
    created_by: Optional[pyUUID]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    sha256_hash: Optional[str] = None


class AssetListItem(BaseModel):
    """Schema for asset list item (summary)."""

    id: pyUUID
    name: str
    thumbnail_url: Optional[str] = None
    processing_status: str
    category: Optional[str]
    tags: list[str]
    view_count: int
    created_at: datetime
