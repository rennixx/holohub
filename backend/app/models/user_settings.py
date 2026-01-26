"""
User Settings Model

Stores user-specific preferences and settings.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.db.base import Base
from app.models import TimestampMixin


class ThemePreference:
    """Theme preference constants."""
    DARK = "dark"
    LIGHT = "light"
    SYSTEM = "system"


class ViewMode:
    """View mode constants."""
    GRID = "grid"
    LIST = "list"


class UserSettings(Base, TimestampMixin):
    """
    User Settings model.

    Stores user preferences for notifications, display, and behavior.
    Each user has exactly one settings record (one-to-one relationship).

    Attributes:
        id: Primary key
        user_id: Foreign key to users table
        user: Relationship to User model

        # Notification Preferences
        email_notifications: Enable email notifications
        push_notifications: Enable push notifications
        device_alerts: Enable device-related alerts
        playlist_updates: Enable playlist update notifications
        team_invites: Enable team invitation notifications

        # Display Preferences
        theme: Visual theme preference (dark/light/system)
        language: UI language code
        timezone: User's timezone
        date_format: Date display format

        # Default Behaviors
        default_view_mode: Default view for assets/playlists (grid/list)
        items_per_page: Default pagination size
        auto_refresh_devices: Auto-refresh device status
        auto_refresh_interval: Refresh interval in seconds

        # Privacy
        profile_visible: Profile visible to other team members
        activity_visible: Activity visible to other team members
    """

    __tablename__ = "user_settings"

    # Primary key and foreign key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    # Relationship to User
    user: Mapped["User"] = relationship("User", back_populates="settings", single_parent=True)

    # Notification Preferences
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    push_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    device_alerts: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    playlist_updates: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    team_invites: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Display Preferences
    theme: Mapped[str] = mapped_column(
        Enum(ThemePreference.DARK, ThemePreference.LIGHT, ThemePreference.SYSTEM, name="theme_preference"),
        default=ThemePreference.DARK,
        nullable=False,
    )
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    date_format: Mapped[str] = mapped_column(String(20), default="MM/DD/YYYY", nullable=False)

    # Default Behaviors
    default_view_mode: Mapped[str] = mapped_column(
        Enum(ViewMode.GRID, ViewMode.LIST, name="view_mode"),
        default=ViewMode.GRID,
        nullable=False,
    )
    items_per_page: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    auto_refresh_devices: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_refresh_interval: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    # Privacy
    profile_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    activity_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<UserSettings(user_id={self.user_id}, theme={self.theme})>"
