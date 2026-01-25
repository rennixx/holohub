"""
Playlist Fetcher

Fetch playlists and playlist items from the HoloHub backend.
Handles authentication, caching, and error recovery.
"""
import logging
import time
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class PlaylistItem:
    """Playlist item data."""

    id: str
    asset_id: str
    position: int
    duration_seconds: int
    asset_file_path: str
    asset_file_size: int
    asset_mime_type: str
    custom_settings: Dict[str, Any]
    transition_override: Optional[str] = None


@dataclass
class Playlist:
    """Playlist data."""

    id: str
    name: str
    description: Optional[str]
    loop_mode: bool
    shuffle: bool
    transition_type: str
    transition_duration_ms: int
    is_active: bool
    total_duration_sec: Optional[int]
    item_count: int
    items: List[PlaylistItem]


class PlaylistFetcher:
    """
    Fetch and manage playlists from the backend.
    """

    def __init__(self, api_client, polling_interval_sec: int = 60):
        """
        Initialize playlist fetcher.

        Args:
            api_client: DeviceAPIClient instance
            polling_interval_sec: How often to check for playlist updates
        """
        self.api_client = api_client
        self.polling_interval_sec = polling_interval_sec
        self.current_playlist: Optional[Playlist] = None
        self.last_fetch_time: Optional[datetime] = None
        self.device_id: Optional[str] = None

    def fetch_assigned_playlist(self, device_id: str) -> Optional[Playlist]:
        """
        Fetch the currently assigned playlist for this device.

        Args:
            device_id: Device ID

        Returns:
            Playlist object or None if no playlist assigned
        """
        self.device_id = device_id

        try:
            # Ensure we're authenticated
            if not self.api_client.is_authenticated:
                logger.info("Not authenticated, fetching device token...")
                self.api_client.authenticate()

            # Fetch playlist from backend
            logger.info(f"Fetching playlist for device {device_id}...")
            response = self.api_client.get_assigned_playlist()

            if response is None:
                logger.info("No playlist assigned to this device")
                self.current_playlist = None
                return None

            # Parse response
            items = []
            for item_data in response.get("items", []):
                item = PlaylistItem(
                    id=item_data["id"],
                    asset_id=item_data["asset_id"],
                    position=item_data["position"],
                    duration_seconds=item_data["duration_seconds"],
                    asset_file_path=item_data["asset_file_path"],
                    asset_file_size=item_data["asset_file_size"],
                    asset_mime_type=item_data["asset_mime_type"],
                    custom_settings=item_data.get("custom_settings", {}),
                    transition_override=item_data.get("transition_override"),
                )
                items.append(item)

            playlist = Playlist(
                id=response["id"],
                name=response["name"],
                description=response.get("description"),
                loop_mode=response["loop_mode"],
                shuffle=response["shuffle"],
                transition_type=response["transition_type"],
                transition_duration_ms=response["transition_duration_ms"],
                is_active=response["is_active"],
                total_duration_sec=response.get("total_duration_sec"),
                item_count=response["item_count"],
                items=items,
            )

            self.current_playlist = playlist
            self.last_fetch_time = datetime.now()

            logger.info(f"Fetched playlist '{playlist.name}' with {playlist.item_count} items")
            return playlist

        except Exception as e:
            logger.error(f"Failed to fetch playlist: {e}")
            self.current_playlist = None
            return None

    def has_playlist_changed(self, new_playlist: Playlist) -> bool:
        """
        Check if playlist has changed since last fetch.

        Args:
            new_playlist: New playlist data

        Returns:
            True if playlist has changed
        """
        if self.current_playlist is None:
            return new_playlist is not None

        if new_playlist is None:
            return True

        # Compare basic properties
        if self.current_playlist.id != new_playlist.id:
            return True

        if self.current_playlist.item_count != new_playlist.item_count:
            return True

        # Compare items
        if len(self.current_playlist.items) != len(new_playlist.items):
            return True

        for current_item, new_item in zip(self.current_playlist.items, new_playlist.items):
            if current_item.asset_id != new_item.asset_id:
                return True
            if current_item.duration_seconds != new_item.duration_seconds:
                return True

        return False

    def should_refresh(self) -> bool:
        """
        Check if playlist should be refreshed based on time.

        Returns:
            True if refresh is needed
        """
        if self.last_fetch_time is None:
            return True

        elapsed = (datetime.now() - self.last_fetch_time).total_seconds()
        return elapsed >= self.polling_interval_sec

    def get_current_item(self) -> Optional[PlaylistItem]:
        """
        Get the current item to display based on playlist position.

        For now, returns the first item. In shuffle mode, would return random item.

        Returns:
            Current PlaylistItem or None
        """
        if self.current_playlist is None or not self.current_playlist.items:
            return None

        # TODO: Implement shuffle mode and position tracking
        # For now, return first item
        return self.current_playlist.items[0]

    def get_all_items(self) -> List[PlaylistItem]:
        """
        Get all items in the current playlist.

        Returns:
            List of PlaylistItem objects
        """
        if self.current_playlist is None:
            return []

        return self.current_playlist.items

    def clear_playlist(self) -> None:
        """Clear the current playlist."""
        self.current_playlist = None
        logger.info("Playlist cleared")

    def get_next_item(self, current_item_id: str) -> Optional[PlaylistItem]:
        """
        Get the next item in the playlist.

        Args:
            current_item_id: Current playlist item ID

        Returns:
            Next PlaylistItem or None
        """
        if self.current_playlist is None:
            return None

        items = self.current_playlist.items
        if not items:
            return None

        # Find current item index
        for i, item in enumerate(items):
            if item.id == current_item_id:
                # Return next item, or first if at end
                if self.current_playlist.loop_mode:
                    return items[(i + 1) % len(items)]
                elif i < len(items) - 1:
                    return items[i + 1]
                else:
                    return None  # End of non-looping playlist

        # If current item not found, return first
        return items[0] if items else None
