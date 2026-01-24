"""
Organizations API

Endpoints for managing organizations and getting stats.
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func

from app.api.deps import CurrentUser, DBSession
from app.models import Asset, Device, Organization, Playlist, User

router = APIRouter()


# =============================================================================
# Schemas
# =============================================================================
class OrganizationStats(BaseModel):
    """Organization statistics."""

    total_assets: int
    total_devices: int
    total_playlists: int
    total_users: int
    storage_used_bytes: int
    storage_usage_percent: float


class OrganizationResponse(BaseModel):
    """Organization response."""

    id: str
    name: str
    slug: str
    tier: str
    storage_quota_gb: int
    storage_used_gb: float

    model_config = {"from_attributes": True}


# =============================================================================
# Endpoints
# =============================================================================
@router.get("/current", response_model=OrganizationResponse)
async def get_current_organization(
    current_user: CurrentUser,
    db: DBSession,
) -> OrganizationResponse:
    """
    Get current user's organization.

    Returns the organization details for the currently authenticated user.
    """
    result = await db.execute(select(Organization).where(Organization.id == current_user.organization_id))
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        slug=org.slug,
        tier=org.tier,
        storage_quota_gb=org.storage_quota_gb,
        storage_used_gb=float(org.storage_used_gb),
    )


@router.get("/current/stats", response_model=OrganizationStats)
async def get_organization_stats(
    current_user: CurrentUser,
    db: DBSession,
) -> OrganizationStats:
    """
    Get organization statistics.

    Returns counts and usage statistics for the organization.
    """
    org_id = current_user.organization_id

    # Get counts for various resources
    assets_result = await db.execute(
        select(func.count()).select_from(Asset).where(
            Asset.organization_id == org_id,
            Asset.deleted_at.is_(None),
        )
    )
    total_assets = assets_result.scalar() or 0

    devices_result = await db.execute(
        select(func.count()).select_from(Device).where(
            Device.organization_id == org_id,
            Device.deleted_at.is_(None),
        )
    )
    total_devices = devices_result.scalar() or 0

    playlists_result = await db.execute(
        select(func.count()).select_from(Playlist).where(
            Playlist.organization_id == org_id,
            Playlist.deleted_at.is_(None),
        )
    )
    total_playlists = playlists_result.scalar() or 0

    users_result = await db.execute(
        select(func.count()).select_from(User).where(
            User.organization_id == org_id,
            User.deleted_at.is_(None),
        )
    )
    total_users = users_result.scalar() or 0

    # Get storage usage
    org_result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = org_result.scalar_one_or_none()

    storage_used_bytes = int((org.storage_used_gb if org else 0) * 1024 * 1024 * 1024)
    storage_quota_gb = org.storage_quota_gb if org else 100
    storage_usage_percent = (org.storage_used_gb / storage_quota_gb) if org and storage_quota_gb > 0 else 0

    return OrganizationStats(
        total_assets=total_assets,
        total_devices=total_devices,
        total_playlists=total_playlists,
        total_users=total_users,
        storage_used_bytes=storage_used_bytes,
        storage_usage_percent=storage_usage_percent,
    )
