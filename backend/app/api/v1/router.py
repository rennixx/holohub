"""
API v1 Router

Aggregates all v1 API routes.
"""
from fastapi import APIRouter

from app.api.v1 import auth
from app.core.config import get_settings

settings = get_settings()

api_router = APIRouter(prefix=settings.api_v1_prefix)

# Include auth routes
api_router.include_router(auth.router)

# TODO: Include other routes when created
# api_router.include_router(organizations.router, prefix="/organizations", tags=["Organizations"])
# api_router.include_router(users.router, prefix="/users", tags=["Users"])
# api_router.include_router(devices.router, prefix="/devices", tags=["Devices"])
# api_router.include_router(assets.router, prefix="/assets", tags=["Assets"])
# api_router.include_router(playlists.router, prefix="/playlists", tags=["Playlists"])
