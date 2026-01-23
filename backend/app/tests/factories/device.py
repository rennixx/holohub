"""
Device Factory

Factory Boy factory for creating test Device instances.
"""
import factory
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_device_secret
from app.models import Device
from app.tests.factories.organization import OrganizationFactory


class DeviceFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Device instances."""

    class Meta:
        model = Device
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"

    name = factory.Faker("sentence", nb_words=3)
    hardware_type = "looking_glass_portrait"
    hardware_id = factory.Faker("mac_address")
    device_secret_hash = factory.LazyAttribute(lambda o: hash_device_secret("test_device_secret_123"))
    status = "pending"
    location_metadata = {}
    tags = []
    display_config = {
        "resolution": {"width": 1536, "height": 2048},
        "orientation": "portrait",
        "quilt_format": {"cols": 8, "rows": 6, "views": 48},
        "brightness": 80,
    }
    network_info = {}
    firmware_version = None
    client_version = None
    current_playlist_id = None
    current_asset_id = None
    playback_position = None
    storage_capacity_gb = 64
    storage_used_gb = 0

    # Organization relation
    organization = factory.SubFactory(OrganizationFactory)


class ActiveDeviceFactory(DeviceFactory):
    """Factory for creating active devices."""

    status = "active"


class OnlineDeviceFactory(ActiveDeviceFactory):
    """Factory for creating online devices."""

    status = "active"
    from datetime import datetime, timedelta

    last_heartbeat = factory.LazyAttribute(lambda o: datetime.now() - timedelta(minutes=1))
