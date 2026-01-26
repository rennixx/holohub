"""
Settings Schemas

Pydantic schemas for user and organization settings validation and serialization.
"""
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# =============================================================================
# User Settings Schemas
# =============================================================================

class ThemePreference:
    """Theme preference constants."""
    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"


class ViewMode:
    """View mode constants."""
    GRID = "grid"
    LIST = "list"


class UserSettingsBase(BaseModel):
    """Base user settings schema."""

    # Notification Preferences
    email_notifications: bool = True
    push_notifications: bool = True
    device_alerts: bool = True
    playlist_updates: bool = True
    team_invites: bool = True

    # Display Preferences
    theme: str = Field(default=ThemePreference.DARK, pattern="^(dark|light|system)$")
    language: str = Field(default="en", min_length=2, max_length=10)
    timezone: str = Field(default="UTC", min_length=1, max_length=50)
    date_format: str = Field(default="MM/DD/YYYY", max_length=20)

    # Default Behaviors
    default_view_mode: str = Field(default=ViewMode.GRID, pattern="^(grid|list)$")
    items_per_page: int = Field(default=20, ge=5, le=100)
    auto_refresh_devices: bool = True
    auto_refresh_interval: int = Field(default=30, ge=5, le=300)

    # Privacy
    profile_visible: bool = True
    activity_visible: bool = True

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validate timezone format."""
        # Basic validation - could be enhanced with pytz
        if not v or len(v.strip()) == 0:
            return "UTC"
        return v.strip()


class UserSettingsUpdate(UserSettingsBase):
    """Schema for updating user settings (all fields optional)."""

    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    device_alerts: Optional[bool] = None
    playlist_updates: Optional[bool] = None
    team_invites: Optional[bool] = None

    # Display Preferences
    theme: Optional[str] = Field(default=None, pattern="^(dark|light|system)$")
    language: Optional[str] = Field(default=None, min_length=2, max_length=10)
    timezone: Optional[str] = Field(default=None, min_length=1, max_length=50)
    date_format: Optional[str] = Field(default=None, max_length=20)

    # Default Behaviors
    default_view_mode: Optional[str] = Field(default=None, pattern="^(grid|list)$")
    items_per_page: Optional[int] = Field(default=None, ge=5, le=100)
    auto_refresh_devices: Optional[bool] = None
    auto_refresh_interval: Optional[int] = Field(default=None, ge=5, le=300)

    # Privacy
    profile_visible: Optional[bool] = None
    activity_visible: Optional[bool] = None


class UserSettingsResponse(UserSettingsBase):
    """Schema for user settings response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: str
    updated_at: str


# =============================================================================
# Organization Settings Schemas
# =============================================================================

class OrgSettingsBase(BaseModel):
    """Base organization settings schema."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: Optional[str] = Field(None, max_length=100, pattern="^[a-z0-9-]+$")
    branding: Optional[dict[str, Any]] = None
    allowed_domains: Optional[list[str]] = None
    default_device_settings: Optional[dict[str, Any]] = None


class OrgSettingsUpdate(BaseModel):
    """Schema for updating organization settings."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, max_length=100, pattern="^[a-z0-9-]+$")
    branding: Optional[dict[str, Any]] = None
    allowed_domains: Optional[list[str]] = None
    default_device_settings: Optional[dict[str, Any]] = None

    @field_validator("branding")
    @classmethod
    def validate_branding(cls, v: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
        """Validate branding settings."""
        if v is None:
            return v

        # Validate logo_url if present
        if "logo_url" in v and v["logo_url"]:
            from pydantic import HttpUrl

            try:
                HttpUrl(v["logo_url"])
            except Exception:
                raise ValueError("logo_url must be a valid URL")

        # Validate primary_color if present (hex color)
        if "primary_color" in v and v["primary_color"]:
            color = v["primary_color"]
            if not color.startswith("#") or len(color) not in [4, 7]:
                raise ValueError("primary_color must be a valid hex color (e.g., #8b5cf6)")

        return v

    @field_validator("allowed_domains")
    @classmethod
    def validate_allowed_domains(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Validate allowed email domains."""
        if v is None:
            return v

        for domain in v:
            if not domain or "." not in domain:
                raise ValueError(f"'{domain}' is not a valid domain")

        return v


class OrgSettingsResponse(OrgSettingsBase):
    """Schema for organization settings response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: str
    updated_at: str


# =============================================================================
# Logo Upload Schemas
# =============================================================================

class LogoUploadResponse(BaseModel):
    """Schema for logo upload response."""

    logo_url: str
    message: str = "Logo uploaded successfully"


class SettingsErrorResponse(BaseModel):
    """Schema for settings error response."""

    error: str
    detail: Optional[dict[str, Any]] = None
