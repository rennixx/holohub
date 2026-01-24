"""
Organization Model

Represents a tenant organization in the HoloHub multi-tenant system.
"""
from datetime import datetime
from typing import Optional

from pydantic import EmailStr
from sqlalchemy import JSON, Column, Enum, String, Text, Integer, Numeric, Boolean
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid4
from uuid_utils.compat import UUID as pyUUID

from app.db.base import Base
from app.models import SoftDeleteMixin, TimestampMixin


class OrganizationTier:
    """Organization tier constants."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Organization(Base, TimestampMixin, SoftDeleteMixin):
    """
    Organization model representing a tenant in the multi-tenant system.

    Each organization has its own users, devices, assets, and playlists
    with complete data isolation through row-level security.

    Attributes:
        id: Unique organization identifier
        name: Organization display name
        slug: URL-friendly identifier for subdomain (e.g., acme.holohub.com)
        tier: Subscription tier (free/pro/enterprise)
        storage_quota_gb: Maximum storage in GB
        storage_used_gb: Current storage usage
        device_limit: Maximum number of devices allowed
        stripe_customer_id: Stripe customer ID for billing
        subscription_status: Current subscription status
        subscription_end_date: When subscription expires
        branding: JSON object with customization options
        allowed_domains: Email domains allowed for SSO
    """

    __tablename__ = "organizations"

    # Primary key
    id: Mapped[pyUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    # Subscription/Tier management
    tier: Mapped[str] = mapped_column(
        Enum(OrganizationTier.FREE, OrganizationTier.PRO, OrganizationTier.ENTERPRISE, name="organization_tier"),
        default=OrganizationTier.FREE,
        nullable=False,
        index=True,
    )

    storage_quota_gb: Mapped[int] = mapped_column(
        Integer,
        default=50,
        nullable=False,
    )

    storage_used_gb: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0,
        nullable=False,
    )

    device_limit: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )

    # Billing
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    subscription_status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )  # 'active', 'past_due', 'canceled', 'incomplete', etc.

    subscription_end_date: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
    )

    # Settings
    branding: Mapped[dict] = mapped_column(
        JSON,
        default={},
        nullable=False,
    )  # {"logo_url": "...", "primary_color": "#FF5733"}

    allowed_domains: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=[],
        nullable=False,
    )  # Email domain whitelist for SSO

    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    devices = relationship("Device", back_populates="organization", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="organization", cascade="all, delete-orphan")
    playlists = relationship("Playlist", back_populates="organization", cascade="all, delete-orphan")

    # Indexes for soft delete
    __table_args__ = (
        # Index for active orgs (not soft deleted)
        # Note: sqlalchemy 2.0 doesn't support partial indexes via orm,
        # need to use raw SQL in migration
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name}, slug={self.slug}, tier={self.tier})>"

    # =============================================================================
    # Storage Management
    # =============================================================================
    @property
    def storage_usage_percent(self) -> float:
        """Get storage usage as a percentage."""
        if self.storage_quota_gb == 0:
            return 0.0
        return (self.storage_used_gb / self.storage_quota_gb) * 100

    @property
    def storage_available_gb(self) -> float:
        """Get available storage in GB."""
        return max(0, self.storage_quota_gb - self.storage_used_gb)

    @property
    def is_storage_full(self) -> bool:
        """Check if storage quota is exceeded."""
        return self.storage_used_gb >= self.storage_quota_gb

    @property
    def is_storage_near_limit(self, threshold: float = 0.9) -> bool:
        """
        Check if storage is near the limit.

        Args:
            threshold: Threshold percentage (default 90%)

        Returns:
            True if usage exceeds threshold
        """
        return self.storage_usage_percent >= (threshold * 100)

    def can_store_asset(self, size_gb: float) -> bool:
        """
        Check if organization can store an asset of given size.

        Args:
            size_gb: Asset size in GB

        Returns:
            True if there's enough space
        """
        return (self.storage_used_gb + size_gb) <= self.storage_quota_gb

    # =============================================================================
    # Device Management
    # =============================================================================
    @property
    def device_count(self) -> int:
        """Get current number of active devices."""
        # This would typically be cached or calculated differently
        # For now, returns the limit
        return len([d for d in self.devices if d.deleted_at is None])

    @property
    def can_add_device(self) -> bool:
        """Check if organization can add more devices."""
        return self.device_count < self.device_limit

    # =============================================================================
    # Subscription Management
    # =============================================================================
    @property
    def is_subscription_active(self) -> bool:
        """Check if subscription is active and not expired."""
        if self.subscription_status != "active":
            return False
        if self.subscription_end_date and self.subscription_end_date < datetime.now():
            return False
        return True

    def upgrade_tier(self, new_tier: str, storage_quota: int, device_limit: int) -> None:
        """
        Upgrade organization to a new tier.

        Args:
            new_tier: New tier (pro/enterprise)
            storage_quota: New storage quota in GB
            device_limit: New device limit
        """
        from app.models.organization import OrganizationTier

        valid_tiers = [OrganizationTier.PRO, OrganizationTier.ENTERPRISE]
        if new_tier not in valid_tiers:
            raise ValueError(f"Invalid tier: {new_tier}")

        self.tier = new_tier
        self.storage_quota_gb = storage_quota
        self.device_limit = device_limit

    # =============================================================================
    # Branding
    # =============================================================================
    @property
    def logo_url(self) -> Optional[str]:
        """Get organization logo URL."""
        return self.branding.get("logo_url")

    @property
    def primary_color(self) -> str:
        """Get organization primary color."""
        return self.branding.get("primary_color", "#000000")

    def set_branding(
        self,
        logo_url: Optional[str] = None,
        primary_color: Optional[str] = None,
        **kwargs,
    ) -> None:
        """
        Update organization branding.

        Args:
            logo_url: URL to organization logo
            primary_color: Primary brand color (hex)
            **kwargs: Additional branding options
        """
        if logo_url:
            self.branding["logo_url"] = logo_url
        if primary_color:
            self.branding["primary_color"] = primary_color
        self.branding.update(kwargs)
