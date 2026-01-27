"""
Billing API

Endpoints for billing, subscription, and invoice management.
"""
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, desc

from app.api.deps import CurrentUser, DBSession
from app.models import Device, Invoice, Organization, Playlist

router = APIRouter()


# =============================================================================
# Schemas
# =============================================================================

class PlanDetails(BaseModel):
    """Plan/tier details."""

    id: str
    name: str
    price: str
    period: str
    description: str
    features: list[str]
    limits: dict[str, Any]
    is_current: bool = False


class UsageStats(BaseModel):
    """Current usage statistics."""

    devices: int
    device_limit: int
    playlists: int
    playlist_limit: int
    storage_gb: float
    storage_limit_gb: int
    storage_percentage: float


class InvoiceItem(BaseModel):
    """Invoice item for display."""

    id: str
    date: str
    amount: float
    currency: str
    status: str
    description: str
    invoice_pdf: Optional[str] = None


class SubscriptionInfo(BaseModel):
    """Current subscription information."""

    tier: str
    status: Optional[str] = None
    subscription_end_date: Optional[str] = None
    is_active: bool
    plan: PlanDetails


# =============================================================================
# Plan Definitions
# =============================================================================

PLAN_DEFINITIONS = {
    "free": {
        "id": "free",
        "name": "Free",
        "price": "$0",
        "period": "forever",
        "description": "For individuals and small teams",
        "features": [
            "Up to 3 devices",
            "Up to 5 playlists",
            "Basic support",
            "Community forum access",
        ],
        "limits": {
            "devices": 3,
            "playlists": 5,
            "storage_gb": 10,
        },
    },
    "pro": {
        "id": "pro",
        "name": "Pro",
        "price": "$29",
        "period": "/month",
        "description": "For growing teams and businesses",
        "features": [
            "Up to 50 devices",
            "Unlimited playlists",
            "Priority support",
            "Advanced analytics",
            "API access",
        ],
        "limits": {
            "devices": 50,
            "playlists": 9999,
            "storage_gb": 100,
        },
    },
    "enterprise": {
        "id": "enterprise",
        "name": "Enterprise",
        "price": "Custom",
        "period": "contact sales",
        "description": "For large organizations",
        "features": [
            "Unlimited everything",
            "Dedicated support",
            "Custom integrations",
            "SLA guarantee",
            "White-label options",
        ],
        "limits": {
            "devices": 9999,
            "playlists": 9999,
            "storage_gb": 1000,
        },
    },
}


def get_plan_limits(tier: str) -> dict[str, Any]:
    """Get plan limits by tier."""
    return PLAN_DEFINITIONS.get(tier, PLAN_DEFINITIONS["free"])["limits"]


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/subscription", response_model=SubscriptionInfo)
async def get_subscription(
    current_user: CurrentUser,
    db: DBSession,
) -> SubscriptionInfo:
    """
    Get current subscription information.

    Returns the current tier, plan details, and subscription status.
    """
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    plan_def = PLAN_DEFINITIONS.get(org.tier, PLAN_DEFINITIONS["free"])

    return SubscriptionInfo(
        tier=org.tier,
        status=org.subscription_status,
        subscription_end_date=org.subscription_end_date.isoformat() if org.subscription_end_date else None,
        is_active=org.is_subscription_active,
        plan=PlanDetails(
            **plan_def,
            is_current=True,
        ),
    )


@router.get("/usage", response_model=UsageStats)
async def get_usage(
    current_user: CurrentUser,
    db: DBSession,
) -> UsageStats:
    """
    Get current usage statistics.

    Returns device, playlist, and storage usage.
    """
    org_id = current_user.organization_id

    # Get organization
    org_result = await db.execute(
        select(Organization).where(Organization.id == org_id)
    )
    org = org_result.scalar_one_or_none()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Get plan limits
    limits = get_plan_limits(org.tier)

    # Count active devices
    devices_result = await db.execute(
        select(Device.__table__.c.id).where(
            Device.organization_id == org_id,
            Device.deleted_at.is_(None),
        )
    )
    device_count = len(devices_result.all())

    # Count playlists
    playlists_result = await db.execute(
        select(Playlist.__table__.c.id).where(
            Playlist.organization_id == org_id,
            Playlist.deleted_at.is_(None),
        )
    )
    playlist_count = len(playlists_result.all())

    storage_used = float(org.storage_used_gb) if org.storage_used_gb else 0
    storage_limit = limits["storage_gb"]

    return UsageStats(
        devices=device_count,
        device_limit=limits["devices"],
        playlists=playlist_count,
        playlist_limit=limits["playlists"],
        storage_gb=round(storage_used, 1),
        storage_limit_gb=storage_limit,
        storage_percentage=round((storage_used / storage_limit) * 100, 1) if storage_limit > 0 else 0,
    )


@router.get("/invoices", response_model=list[InvoiceItem])
async def get_invoices(
    current_user: CurrentUser,
    db: DBSession,
    limit: int = 12,
) -> list[InvoiceItem]:
    """
    Get invoice history.

    Returns a list of invoices for the organization.
    """
    org_id = current_user.organization_id

    result = await db.execute(
        select(Invoice)
        .where(
            Invoice.organization_id == org_id,
            Invoice.deleted_at.is_(None),
        )
        .order_by(desc(Invoice.created_at))
        .limit(limit)
    )
    invoices = result.scalars().all()

    return [
        InvoiceItem(
            id=str(invoice.id),
            date=invoice.created_at.strftime("%Y-%m-%d"),
            amount=float(invoice.amount),
            currency=invoice.currency,
            status=invoice.status,
            description=invoice.description or f"Invoice #{invoice.id}",
            invoice_pdf=invoice.invoice_pdf,
        )
        for invoice in invoices
    ]


@router.get("/plans", response_model=list[PlanDetails])
async def get_plans(
    current_user: CurrentUser,
    db: DBSession,
) -> list[PlanDetails]:
    """
    Get available plans.

    Returns all available plans with current plan marked.
    """
    # Get current organization tier
    result = await db.execute(
        select(Organization.tier).where(Organization.id == current_user.organization_id)
    )
    current_tier = result.scalar_one_or_none() or "free"

    return [
        PlanDetails(
            **plan_def,
            is_current=(plan_id == current_tier),
        )
        for plan_id, plan_def in PLAN_DEFINITIONS.items()
    ]


class UpgradeRequest(BaseModel):
    """Request to upgrade plan."""

    tier: str


@router.post("/upgrade")
async def upgrade_plan(
    request: UpgradeRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> dict[str, str]:
    """
    Upgrade to a new plan.

    This would typically integrate with Stripe for payment processing.
    For now, it's a simplified version.
    """
    if request.tier not in ["pro", "enterprise"]:
        raise HTTPException(status_code=400, detail="Invalid tier")

    # Get organization
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Get plan limits
    limits = get_plan_limits(request.tier)

    # Update organization
    org.tier = request.tier
    org.storage_quota_gb = limits["storage_gb"]
    org.device_limit = limits["devices"]
    org.subscription_status = "active"
    # Set subscription end date to 1 month from now
    from datetime import timedelta
    org.subscription_end_date = datetime.now() + timedelta(days=30)

    await db.commit()

    return {
        "message": f"Successfully upgraded to {request.tier} plan",
        "tier": request.tier,
    }
