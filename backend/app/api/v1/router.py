"""
API v1 Router

Aggregates all v1 API routes.
"""
from fastapi import APIRouter

from app.api.v1 import auth, organizations, assets, devices, playlists, settings
from app.core.config import get_settings

settings_config = get_settings()

api_router = APIRouter(prefix=settings_config.api_v1_prefix)

# Include auth routes
api_router.include_router(auth.router)

# Include organizations routes
api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])

# Include assets routes
api_router.include_router(assets.router, prefix="/assets", tags=["Assets"])

# Include devices routes
api_router.include_router(devices.router, prefix="/devices", tags=["Devices"])

# Include playlists routes
api_router.include_router(playlists.router, prefix="/playlists", tags=["Playlists"])

# Include settings routes
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])

# TODO: Include other routes when created
# api_router.include_router(users.router, prefix="/users", tags=["Users"])
