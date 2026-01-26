"""
Settings API

Endpoints for managing user and organization settings.
"""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DBSession, require_admin
from app.models import Organization, User, UserSettings
from app.schemas.settings import (
    OrgSettingsUpdate,
    OrgSettingsResponse,
    ThemePreference,
    UserSettingsResponse,
    UserSettingsUpdate,
    ViewMode,
)

router = APIRouter()


# =============================================================================
# User Settings Endpoints
# =============================================================================


@router.get("", response_model=UserSettingsResponse)
async def get_user_settings(
    current_user: CurrentUser,
    db: DBSession,
) -> UserSettings:
    """
    Get current user's settings.

    Returns the user's preference settings.
    If no settings exist, creates default settings.
    """
    # Try to get existing settings
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()

    # Create default settings if none exist
    if settings is None:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return UserSettingsResponse(
        id=settings.id,
        user_id=settings.user_id,
        email_notifications=settings.email_notifications,
        push_notifications=settings.push_notifications,
        device_alerts=settings.device_alerts,
        playlist_updates=settings.playlist_updates,
        team_invites=settings.team_invites,
        theme=settings.theme,
        language=settings.language,
        timezone=settings.timezone,
        date_format=settings.date_format,
        default_view_mode=settings.default_view_mode,
        items_per_page=settings.items_per_page,
        auto_refresh_devices=settings.auto_refresh_devices,
        auto_refresh_interval=settings.auto_refresh_interval,
        profile_visible=settings.profile_visible,
        activity_visible=settings.activity_visible,
        created_at=settings.created_at.isoformat(),
        updated_at=settings.updated_at.isoformat(),
    )


@router.put("", response_model=UserSettingsResponse)
async def update_user_settings(
    updates: UserSettingsUpdate,
    current_user: CurrentUser,
    db: DBSession,
) -> UserSettings:
    """
    Update current user's settings.

    All fields are optional. Only provided fields will be updated.
    """
    # Get existing settings
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()

    # Create default settings if none exist
    if settings is None:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)

    # Update only provided fields
    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)

    await db.commit()
    await db.refresh(settings)

    return UserSettingsResponse(
        id=settings.id,
        user_id=settings.user_id,
        email_notifications=settings.email_notifications,
        push_notifications=settings.push_notifications,
        device_alerts=settings.device_alerts,
        playlist_updates=settings.playlist_updates,
        team_invites=settings.team_invites,
        theme=settings.theme,
        language=settings.language,
        timezone=settings.timezone,
        date_format=settings.date_format,
        default_view_mode=settings.default_view_mode,
        items_per_page=settings.items_per_page,
        auto_refresh_devices=settings.auto_refresh_devices,
        auto_refresh_interval=settings.auto_refresh_interval,
        profile_visible=settings.profile_visible,
        activity_visible=settings.activity_visible,
        created_at=settings.created_at.isoformat(),
        updated_at=settings.updated_at.isoformat(),
    )


@router.post("/reset", response_model=UserSettingsResponse)
async def reset_user_settings(
    current_user: CurrentUser,
    db: DBSession,
) -> UserSettings:
    """
    Reset current user's settings to defaults.

    Deletes existing settings and creates new default settings.
    """
    # Delete existing settings
    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    settings = result.scalar_one_or_none()

    if settings:
        await db.delete(settings)
        await db.commit()

    # Create new default settings
    settings = UserSettings(user_id=current_user.id)
    db.add(settings)
    await db.commit()
    await db.refresh(settings)

    return UserSettingsResponse(
        id=settings.id,
        user_id=settings.user_id,
        email_notifications=settings.email_notifications,
        push_notifications=settings.push_notifications,
        device_alerts=settings.device_alerts,
        playlist_updates=settings.playlist_updates,
        team_invites=settings.team_invites,
        theme=settings.theme,
        language=settings.language,
        timezone=settings.timezone,
        date_format=settings.date_format,
        default_view_mode=settings.default_view_mode,
        items_per_page=settings.items_per_page,
        auto_refresh_devices=settings.auto_refresh_devices,
        auto_refresh_interval=settings.auto_refresh_interval,
        profile_visible=settings.profile_visible,
        activity_visible=settings.activity_visible,
        created_at=settings.created_at.isoformat(),
        updated_at=settings.updated_at.isoformat(),
    )


# =============================================================================
# Organization Settings Endpoints
# =============================================================================


@router.get("/organization", response_model=OrgSettingsResponse)
async def get_organization_settings(
    current_user: CurrentUser,
    db: DBSession,
) -> Organization:
    """
    Get current organization's settings.

    Returns organization details including branding.
    """
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return OrgSettingsResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        branding=org.branding,
        allowed_domains=org.allowed_domains,
        default_device_settings=org.default_device_settings,
        created_at=org.created_at.isoformat(),
        updated_at=org.updated_at.isoformat(),
    )


@router.put("/organization", response_model=OrgSettingsResponse)
async def update_organization_settings(
    updates: OrgSettingsUpdate,
    current_user: CurrentUser,
    db: DBSession,
) -> Organization:
    """
    Update current organization's settings.

    Only admins and owners can update organization settings.
    """
    # Check permissions
    if not current_user.can_manage_users():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and owners can update organization settings",
        )

    # Get organization
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    # Update only provided fields
    update_data = updates.model_dump(exclude_unset=True)

    # Validate slug uniqueness if provided
    if "slug" in update_data and update_data["slug"] != org.slug:
        existing_result = await db.execute(
            select(Organization).where(
                Organization.slug == update_data["slug"],
                Organization.id != org.id,
            )
        )
        existing = existing_result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization slug already taken",
            )

    for field, value in update_data.items():
        setattr(org, field, value)

    await db.commit()
    await db.refresh(org)

    return OrgSettingsResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        branding=org.branding,
        allowed_domains=org.allowed_domains,
        default_device_settings=org.default_device_settings,
        created_at=org.created_at.isoformat(),
        updated_at=org.updated_at.isoformat(),
    )
