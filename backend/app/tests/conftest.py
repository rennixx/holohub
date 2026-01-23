"""
Pytest Configuration and Fixtures

Contains all shared test fixtures and configuration.
"""
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import get_settings
from app.core.security import create_access_token, create_refresh_token, get_password_hash
from app.db.base import Base, get_db
from app.models import Organization, User, Device, Asset, Playlist
from app.main import app
from uuid_utils.compat import UUID as pyUUID


# =============================================================================
# Test Database Configuration
# =============================================================================
TEST_DATABASE_URL = get_settings().test_database_url or "postgresql+asyncpg://holohub:holohub_test@localhost:5432/holohub_test"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

# Create test session factory
test_session_maker = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """Set up test database schema."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.

    This fixture creates a new session for each test and rolls back
    changes after the test completes.
    """
    async with test_session_maker() as session:
        yield session
    await session.rollback()


# =============================================================================
# Test Client
# =============================================================================
@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test HTTP client.

    This fixture creates an HTTP client that overrides the database
    dependency with the test session.
    """

    async def override_get_db():
        yield db_session

    from app.api.deps import get_db
    from app.main import app

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# =============================================================================
# Auth Fixtures
# =============================================================================
@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user with organization."""
    org = Organization(
        name="Test Organization",
        slug="test-org",
        tier="free",
        storage_quota_gb=50,
        device_limit=10,
    )
    db_session.add(org)
    await db_session.flush()

    user = User(
        email="test@example.com",
        password_hash=get_password_hash("TestPassword123!"),
        full_name="Test User",
        organization_id=org.id,
        role="owner",
        email_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create authentication headers for test user."""
    access_token = create_access_token(test_user.id, test_user.organization_id, test_user.role)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def auth_tokens(test_user: User) -> tuple[str, str]:
    """Create access and refresh tokens for test user."""
    access_token = create_access_token(test_user.id, test_user.organization_id, test_user.role)
    refresh_token = create_refresh_token(test_user.id, test_user.organization_id)
    return access_token, refresh_token


# =============================================================================
# Organization Fixtures
# =============================================================================
@pytest.fixture
async def test_organization(db_session: AsyncSession) -> Organization:
    """Create a test organization."""
    org = Organization(
        name="Test Organization",
        slug="test-org",
        tier="free",
        storage_quota_gb=50,
        device_limit=10,
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def test_organization_pro(db_session: AsyncSession) -> Organization:
    """Create a test organization with pro tier."""
    org = Organization(
        name="Pro Organization",
        slug="pro-org",
        tier="pro",
        storage_quota_gb=500,
        device_limit=100,
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


# =============================================================================
# Device Fixtures
# =============================================================================
@pytest.fixture
async def test_device(db_session: AsyncSession, test_user: User) -> Device:
    """Create a test device."""
    device = Device(
        name="Test Device",
        hardware_type="looking_glass_portrait",
        hardware_id="00:11:22:33:44:55",
        device_secret_hash=get_password_hash("test_device_secret_123"),
        organization_id=test_user.organization_id,
        status="pending",
    )
    db_session.add(device)
    await db_session.commit()
    await db_session.refresh(device)
    return device


# =============================================================================
# Asset Fixtures
# =============================================================================
@pytest.fixture
async def test_asset(db_session: AsyncSession, test_user: User) -> Asset:
    """Create a test asset."""
    asset = Asset(
        name="Test Asset",
        description="A test 3D model",
        organization_id=test_user.organization_id,
        created_by=test_user.id,
        original_url="s3://test-bucket/test.glb",
        file_size_bytes=15000000,
        mime_type="model/gltf-binary",
        processing_status="completed",
        outputs={
            "optimized_glb": {"url": "s3://test-bucket/optimized.glb", "size_bytes": 5000000},
            "thumbnail": {"url": "s3://test-bucket/thumb.jpg", "width": 400, "height": 400},
        },
        cdn_urls={
            "optimized_glb": {"url": "https://cdn.holohub.com/optimized.glb"},
            "thumbnail": {"url": "https://cdn.holohub.com/thumb.jpg"},
        },
        geometry_stats={
            "poly_count": 50000,
            "vertex_count": 25000,
            "has_animations": False,
        },
    )
    db_session.add(asset)
    await db_session.commit()
    await db_session.refresh(asset)
    return asset


# =============================================================================
# Playlist Fixtures
# =============================================================================
@pytest.fixture
async def test_playlist(db_session: AsyncSession, test_user: User, test_asset: Asset) -> Playlist:
    """Create a test playlist with items."""
    playlist = Playlist(
        name="Test Playlist",
        organization_id=test_user.organization_id,
        created_by=test_user.id,
        loop_mode=True,
        shuffle=False,
        transition_type="fade",
        transition_duration_ms=500,
        is_active=True,
        total_duration_sec=20,
        item_count=2,
    )
    db_session.add(playlist)
    await db_session.flush()

    # Add playlist items
    from app.models import PlaylistItem

    item1 = PlaylistItem(
        playlist_id=playlist.id,
        asset_id=test_asset.id,
        position=0,
        duration_seconds=10,
    )
    item2 = PlaylistItem(
        playlist_id=playlist.id,
        asset_id=test_asset.id,
        position=1,
        duration_seconds=10,
    )
    db_session.add_all([item1, item2])
    await db_session.commit()
    await db_session.refresh(playlist)

    return playlist


# =============================================================================
# Mock Fixtures
# =============================================================================
@pytest.fixture
def mock_s3_upload(monkeypatch) -> MagicMock:
    """Mock S3 upload function."""
    mock_upload = AsyncMock(return_value="s3://test-bucket/uploaded.glb")
    monkeypatch.setattr("app.utils.storage.upload_to_s3", mock_upload)
    return mock_upload


@pytest.fixture
def mock_celery_task(monkeypatch) -> MagicMock:
    """Mock Celery task dispatch."""
    mock_task = MagicMock(return_value="task-id-123")
    monkeypatch.setattr("app.tasks.celery_app.process_asset.delay", mock_task)
    return mock_task


# =============================================================================
# Pytest Configuration
# =============================================================================
@pytest.fixture(scope="session")
def test_config():
    """Override settings for testing."""
    from app.core.config import Settings

    return Settings(
        APP_NAME="HoloHub Test",
        APP_ENV="test",
        DEBUG=True,
        DATABASE_URL=TEST_DATABASE_URL,
        SECRET_KEY="test-secret-key-for-testing",
        REDIS_URL="redis://localhost:6379/15",
        RATE_LIMIT_ENABLED=False,
        S3_ENDPOINT="http://localhost:9000",
        S3_ACCESS_KEY="minioadmin",
        S3_SECRET_KEY="minioadmin",
        S3_BUCKET="holohub-test",
    )


# =============================================================================
# Pytest-asyncio Configuration
# =============================================================================
def pytest_configure(config):
    """Configure pytest for async tests."""
    pytest_asyncio_mode = "auto"
    pytest_asyncio_default_fixture_loop_scope = "function"
