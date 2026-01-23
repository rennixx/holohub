"""
Factory Boy Factories Package

Contains all test data factories.
"""
# Import all factories
from app.tests.factories.organization import (
    OrganizationFactory,
    ProOrganizationFactory,
    EnterpriseOrganizationFactory,
)
from app.tests.factories.user import (
    UserFactory,
    AdminUserFactory,
    OwnerUserFactory,
)
from app.tests.factories.device import (
    DeviceFactory,
    ActiveDeviceFactory,
    OnlineDeviceFactory,
)
from app.tests.factories.asset import (
    AssetFactory,
    CompletedAssetFactory,
    ProductAssetFactory,
)
from app.tests.factories.playlist import (
    PlaylistFactory,
    PlaylistWithItemsFactory,
    InactivePlaylistFactory,
)

__all__ = [
    # Organization
    "OrganizationFactory",
    "ProOrganizationFactory",
    "EnterpriseOrganizationFactory",
    # User
    "UserFactory",
    "AdminUserFactory",
    "OwnerUserFactory",
    # Device
    "DeviceFactory",
    "ActiveDeviceFactory",
    "OnlineDeviceFactory",
    # Asset
    "AssetFactory",
    "CompletedAssetFactory",
    "ProductAssetFactory",
    # Playlist
    "PlaylistFactory",
    "PlaylistWithItemsFactory",
    "InactivePlaylistFactory",
]
