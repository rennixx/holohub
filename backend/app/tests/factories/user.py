"""
User Factory

Factory Boy factory for creating test User instances.
"""
import factory
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models import User
from app.tests.factories.organization import OrganizationFactory


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating User instances."""

    class Meta:
        model = User
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"

    email = factory.Faker("email")
    email_verified = False
    password_hash = factory.LazyAttribute(lambda o: get_password_hash("Password123!"))
    full_name = factory.Faker("name")
    avatar_url = None
    role = "viewer"
    permissions = {}
    last_login = None
    last_ip = None
    failed_login_attempts = 0
    locked_until = None
    force_password_reset = False
    mfa_enabled = False
    mfa_secret = None
    backup_codes = []

    # Organization relation
    organization = factory.SubFactory(OrganizationFactory)


class AdminUserFactory(UserFactory):
    """Factory for creating admin users."""

    role = "admin"


class OwnerUserFactory(UserFactory):
    """Factory for creating owner users."""

    role = "owner"
