"""
Organization Schemas

Pydantic schemas for organization validation and serialization.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator

from uuid_utils.compat import UUID as pyUUID


# =============================================================================
# Base Schemas
# =============================================================================
class OrganizationBase(BaseModel):
    """Base organization schema."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Validate slug format."""
        from app.core.security import validate_slug

        if not validate_slug(v):
            raise ValueError(
                "Slug must contain only lowercase letters, numbers, and hyphens. "
                "No consecutive hyphens or leading/trailing hyphens."
            )
        return v.lower()


class OrganizationTierUpdate(BaseModel):
    """Schema for updating organization tier."""

    tier: str = Field(..., pattern="^(free|pro|enterprise)$")


# =============================================================================
# Create Schemas
# =============================================================================
class OrganizationCreate(OrganizationBase):
    """Schema for creating a new organization."""

    # Optional: Provide admin user details during org creation
    admin_name: Optional[str] = Field(None, max_length=255)
    admin_email: Optional[EmailStr] = None
    admin_password: Optional[str] = Field(None, min_length=12)


# =============================================================================
# Update Schemas
# =============================================================================
class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    branding: Optional[dict] = None
    allowed_domains: Optional[list[str]] = None


# =============================================================================
# Response Schemas
# =============================================================================
class OrganizationResponse(OrganizationBase):
    """Schema for organization response."""

    model_config = ConfigDict(from_attributes=True)

    id: pyUUID
    tier: str
    storage_quota_gb: int
    storage_used_gb: float
    device_limit: int
    subscription_status: Optional[str] = None
    subscription_end_date: Optional[datetime] = None
    branding: dict
    allowed_domains: list[str]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @property
    def storage_usage_percent(self) -> float:
        """Calculate storage usage percentage."""
        if self.storage_quota_gb == 0:
            return 0.0
        return (self.storage_used_gb / self.storage_quota_gb) * 100


class OrganizationStats(BaseModel):
    """Organization statistics."""

    total_users: int
    total_devices: int
    total_assets: int
    total_playlists: int
    online_devices: int
    storage_used_gb: float
    storage_quota_gb: int
