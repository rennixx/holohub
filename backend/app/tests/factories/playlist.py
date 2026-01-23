"""
Playlist Factory

Factory Boy factory for creating test Playlist instances.
"""
import factory
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Playlist, PlaylistItem
from app.tests.factories.organization import OrganizationFactory
from app.tests.factories.user import OwnerUserFactory
from app.tests.factories.asset import AssetFactory


class PlaylistFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Playlist instances."""

    class Meta:
        model = Playlist
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"

    name = factory.Faker("sentence", nb_words=2)
    description = factory.Faker("text", max_nb_chars=200)
    loop_mode = True
    shuffle = False
    transition_type = "fade"
    transition_duration_ms = 500
    schedule_config = {}
    is_active = True
    total_duration_sec = 60
    item_count = 3

    # Organization relation
    organization = factory.SubFactory(OrganizationFactory)

    # Created by
    created_by = factory.SubFactory(OwnerUserFactory)


class PlaylistWithItemsFactory(PlaylistFactory):
    """Factory for creating playlists with items."""

    @factory.post_generation
    def create_items(obj, create, extracted, **kwargs):
        """Create playlist items."""
        if not create:
            return

        # Create 3 assets
        assets = [AssetFactory(organization=obj.organization) for _ in range(3)]

        # Create playlist items
        for i, asset in enumerate(assets):
            PlaylistItem(
                playlist_id=obj.id,
                asset_id=asset.id,
                position=i,
                duration_seconds=20,
            )


class InactivePlaylistFactory(PlaylistFactory):
    """Factory for creating inactive playlists."""

    is_active = False
