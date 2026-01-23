"""
Organization Factory

Factory Boy factory for creating test Organization instances.
"""
import factory
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Organization


class OrganizationFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Organization instances."""

    class Meta:
        model = Organization
        sqlalchemy_session = None  # Will be set by conftest
        sqlalchemy_session_persistence = "commit"

    name = factory.Faker("company")
    slug = factory.LazyAttribute(lambda o: o.name.lower().replace(" ", "-").replace(".", "-")[:100])
    tier = "free"
    storage_quota_gb = 50
    storage_used_gb = 0
    device_limit = 10
    stripe_customer_id = None
    subscription_status = None
    subscription_end_date = None
    branding = {}
    allowed_domains = []

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override to use async session if available."""
        # For async session, we need to handle differently
        # This is a simplified version
        return super()._create(model_class, *args, **kwargs)


class ProOrganizationFactory(OrganizationFactory):
    """Factory for creating Pro tier organizations."""

    tier = "pro"
    storage_quota_gb = 500
    device_limit = 100


class EnterpriseOrganizationFactory(OrganizationFactory):
    """Factory for creating Enterprise tier organizations."""

    tier = "enterprise"
    storage_quota_gb = 10000
    device_limit = 1000
