"""
Asset Factory

Factory Boy factory for creating test Asset instances.
"""
import factory
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Asset
from app.tests.factories.organization import OrganizationFactory
from app.tests.factories.user import OwnerUserFactory


class AssetFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating Asset instances."""

    class Meta:
        model = Asset
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"

    name = factory.Faker("sentence", nb_words=2)
    description = factory.Faker("text", max_nb_chars=200)
    original_filename = factory.LazyAttribute(lambda o: f"{o.name}.glb")
    original_url = factory.LazyAttribute(lambda o: f"s3://holohub-source/{o.organization_id}/{o.id}/original.glb")
    original_hash = None
    file_size_bytes = 15000000
    mime_type = "model/gltf-binary"
    processing_status = "pending"
    processing_started_at = None
    processing_completed_at = None
    processing_error = None
    processing_logs = []
    celery_task_id = None
    geometry_stats = {}
    outputs = {}
    cdn_urls = {}
    tags = []
    category = None
    custom_metadata = {}
    is_public = False
    visibility = "private"
    view_count = 0
    download_count = 0
    device_usage_count = 0

    # Organization relation
    organization = factory.SubFactory(OrganizationFactory)

    # Created by
    created_by = factory.SubFactory(OwnerUserFactory)


class CompletedAssetFactory(AssetFactory):
    """Factory for creating assets with completed processing."""

    processing_status = "completed"
    outputs = {
        "optimized_glb": {
            "url": "s3://holohub-processed/optimized.glb",
            "size_bytes": 5000000,
            "poly_count": 50000,
        },
        "draco_compressed": {
            "url": "s3://holohub-processed/draco.glb",
            "size_bytes": 850000,
            "compression_ratio": 2.82,
        },
        "thumbnail": {
            "url": "s3://holohub-processed/thumb.jpg",
            "width": 400,
            "height": 400,
        },
    }
    cdn_urls = {
        "optimized_glb": {
            "url": "https://cdn.holohub.com/optimized.glb",
        },
        "thumbnail": {
            "url": "https://cdn.holohub.com/thumb.jpg",
        },
    }
    geometry_stats = {
        "poly_count": 50000,
        "vertex_count": 25000,
        "triangle_count": 50000,
        "material_count": 2,
        "texture_count": 3,
        "has_animations": False,
    }


class ProductAssetFactory(CompletedAssetFactory):
    """Factory for creating product assets."""

    category = "products"
    tags = ["product", "showcase"]
    custom_metadata = factory.LazyAttribute(
        lambda o: {
            "sku": f"PROD-{o.id.hex[:8].upper()}",
            "price": 299.99,
        }
    )
