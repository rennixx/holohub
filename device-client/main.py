"""
HoloHub Device Client

Main client application for holographic display devices.
Connects to HoloHub backend, downloads content, and displays holograms.
"""
import os
import sys
import time
import signal
import logging
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api_client import DeviceAPIClient
from src.system_metrics import get_system_metrics
from src.content_manager import ContentManager
from src.display_manager import DisplayManager, DisplayConfig, DisplayType
from src.playlist_fetcher import PlaylistFetcher
from src.model_loader import ModelLoader
from config.config import load_config, DISPLAY_TYPES, HARDWARE_TYPE_MAP


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DeviceClient:
    """
    Main HoloHub device client.

    Handles:
    - Device authentication
    - Heartbeat monitoring
    - Content download and caching
    - Playlist execution
    - Command handling
    """

    def __init__(self, config_file: Optional[Path] = None, real_3d: bool = False):
        self.real_3d = real_3d

        # Load configuration
        self.config = load_config(config_file)

        # Validate required configuration
        if not self.config.hardware_id or not self.config.device_secret:
            logger.error(
                "Device credentials not configured. "
                "Set DEVICE_HARDWARE_ID and DEVICE_SECRET environment variables "
                "or add them to config file."
            )
            raise ValueError("Missing device credentials")

        # Initialize components
        self.api_client = DeviceAPIClient(
            api_base_url=self.config.api_base_url,
            hardware_id=self.config.hardware_id,
            device_secret=self.config.device_secret,
            timeout=self.config.api_timeout,
        )

        self.metrics = get_system_metrics()
        self.content_manager = ContentManager(
            cache_dir=self.config.content_cache_dir,
            max_cache_size_gb=self.config.max_cache_size_gb,
        )

        # Initialize playlist fetcher
        self.playlist_fetcher = PlaylistFetcher(
            api_client=self.api_client,
            polling_interval_sec=60,
        )

        # Initialize model loader (for real 3D mode)
        self.model_loader = ModelLoader()

        # Setup display
        display_type = DisplayType(self.config.display_type)
        display_info = DISPLAY_TYPES.get(self.config.display_type, {})
        self.display_config = DisplayConfig(
            display_type=display_type,
            resolution=display_info.get("resolution", self.config.display_resolution),
            quilt_views=display_info.get("quilt_views", self.config.quilt_views),
            quilt_depth=display_info.get("quilt_depth", self.config.quilt_depth),
        )

        self.display: Optional[DisplayManager] = None

        # Runtime state
        self._running = False
        self._current_playlist: Optional[Dict[str, Any]] = None
        self._current_item_index = 0

    def authenticate(self) -> bool:
        """Authenticate device with backend."""
        try:
            token = self.api_client.authenticate()
            logger.info(f"✓ Device authenticated: {token.device_id}")
            logger.info(f"  Organization: {token.organization_id}")
            logger.info(f"  Token expires in: {token.expires_in}s")
            return True
        except Exception as e:
            logger.error(f"✗ Authentication failed: {e}")
            return False

    def send_heartbeat(self) -> bool:
        """Send heartbeat to backend."""
        try:
            # Get system metrics
            metrics_data = self.metrics.get_all_metrics(self.config.api_base_url)

            # Add firmware/client versions
            metrics_data["firmware_version"] = self.config.firmware_version
            metrics_data["client_version"] = self.config.client_version

            # Add current playlist info
            if self._current_playlist:
                metrics_data["current_playlist_id"] = self._current_playlist.get("id")

            # Send heartbeat
            response = self.api_client.send_heartbeat(**metrics_data)

            logger.debug(f"Heartbeat: {response['status']} - {response['message']}")
            return True

        except Exception as e:
            logger.error(f"Heartbeat failed: {e}")
            return False

    def get_assigned_playlist(self) -> Optional[Dict[str, Any]]:
        """Get assigned playlist from backend."""
        try:
            playlist = self.api_client.get_assigned_playlist()
            if playlist:
                logger.info(f"Assigned playlist: {playlist.get('name', 'Unnamed')}")
                items = playlist.get("items", [])
                logger.info(f"  Playlist items: {len(items)}")
            return playlist
        except Exception as e:
            logger.warning(f"Failed to get playlist: {e}")
            return None

    def download_playlist_content(self, playlist: Dict[str, Any]) -> bool:
        """
        Download all content for a playlist.

        Args:
            playlist: Playlist dictionary

        Returns:
            True if all content downloaded successfully
        """
        items = playlist.get("items", [])
        if not items:
            logger.warning("Playlist has no items")
            return True

        logger.info(f"Downloading content for {len(items)} items...")

        success = True
        for i, item in enumerate(items, 1):
            asset_id = item.get("asset_id")
            if not asset_id:
                logger.warning(f"Item {i} missing asset_id")
                continue

            # Check if already cached
            if self.content_manager.is_cached(asset_id):
                logger.info(f"  [{i}/{len(items)}] {asset_id} - cached ✓")
                continue

            # Download with asset data from playlist (skip metadata fetch)
            logger.info(f"  [{i}/{len(items)}] {asset_id} - downloading...")
            asset_data = {
                "file_path": item.get("asset_file_path"),
                "file_size": item.get("asset_file_size"),
                "mime_type": item.get("asset_mime_type", "model/glb"),
            }
            cached = self.content_manager.download_content(
                api_client=self.api_client,
                asset_id=asset_id,
                asset_data=asset_data,
            )

            if not cached:
                logger.error(f"  [{i}/{len(items)}] {asset_id} - failed ✗")
                success = False
            else:
                logger.info(f"  [{i}/{len(items)}] {asset_id} - complete ✓")

        return success

    def display_playlist_item(self, item: Dict[str, Any]) -> bool:
        """
        Display a single playlist item.

        Args:
            item: Playlist item dictionary

        Returns:
            True if successful
        """
        if not self.display:
            return False

        asset_id = item.get("asset_id")
        duration = item.get("duration", 10)  # Default 10 seconds

        logger.info(f"Displaying: {asset_id} ({duration}s)")

        success = self.display.show_playlist_item(item, self.content_manager)

        if success and duration:
            # Wait for duration (or user interrupt)
            try:
                time.sleep(duration)
            except KeyboardInterrupt:
                logger.info("Display interrupted")

        return success

    def execute_playlist(self, playlist: Dict[str, Any]) -> None:
        """
        Execute a playlist - loop through items.

        Args:
            playlist: Playlist dictionary
        """
        items = playlist.get("items", [])
        if not items:
            logger.warning("Playlist has no items to display")
            return

        logger.info(f"Executing playlist: {playlist.get('name', 'Unnamed')}")
        logger.info(f"Items: {len(items)}")

        self._current_playlist = playlist
        self._current_item_index = 0

        try:
            while self._running:
                # Get current item (loop around)
                item = items[self._current_item_index]
                self.display_playlist_item(item)

                # Move to next item
                self._current_item_index = (self._current_item_index + 1) % len(items)

        except Exception as e:
            logger.error(f"Playlist execution error: {e}")

    def initialize_display(self) -> bool:
        """Initialize display backend."""
        try:
            self.display = DisplayManager(
                config=self.display_config,
                simulation_mode=self.config.simulation_mode,
                real_3d=self.real_3d,
            )

            if self.display.initialize():
                logger.info(f"✓ Display initialized: {self.config.display_type}")
                if self.config.simulation_mode:
                    logger.info("  Running in SIMULATION mode")
                return True
            else:
                logger.error("✗ Display initialization failed")
                return False

        except Exception as e:
            logger.error(f"✗ Display error: {e}")
            return False

    def start(self) -> None:
        """Start device client."""
        logger.info("=" * 60)
        logger.info("HoloHub Device Client Starting")
        logger.info("=" * 60)
        logger.info(f"Device: {self.config.hardware_id}")
        logger.info(f"Server: {self.config.api_base_url}")
        logger.info(f"Display: {self.config.display_type}")
        logger.info(f"Mode: {'Simulation' if self.config.simulation_mode else 'Production'}")
        logger.info("=" * 60)

        self._running = True

        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.stop()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            # Step 1: Authenticate
            if not self.authenticate():
                logger.error("Authentication failed. Exiting.")
                return

            # Step 2: Initialize display
            if not self.initialize_display():
                logger.error("Display initialization failed. Exiting.")
                return

            # Step 3: Get assigned playlist using playlist fetcher
            device_id = self.api_client._token.device_id  # type: ignore
            playlist = self.playlist_fetcher.fetch_assigned_playlist(device_id)
            if not playlist:
                logger.warning("No playlist assigned. Device will run in idle mode.")
                # Could show default content here
                return

            # Convert Playlist dataclass to dict for compatibility
            playlist_dict = {
                "id": playlist.id,
                "name": playlist.name,
                "description": playlist.description,
                "loop_mode": playlist.loop_mode,
                "shuffle": playlist.shuffle,
                "transition_type": playlist.transition_type,
                "transition_duration_ms": playlist.transition_duration_ms,
                "is_active": playlist.is_active,
                "total_duration_sec": playlist.total_duration_sec,
                "item_count": playlist.item_count,
                "items": [
                    {
                        "id": item.id,
                        "asset_id": item.asset_id,
                        "position": item.position,
                        "duration_seconds": item.duration_seconds,
                        "asset_file_path": item.asset_file_path,
                        "asset_file_size": item.asset_file_size,
                        "asset_mime_type": item.asset_mime_type,
                        "custom_settings": item.custom_settings,
                        "transition_override": item.transition_override,
                    }
                    for item in playlist.items
                ],
            }

            # Step 4: Download content
            if not self.download_playlist_content(playlist_dict):
                logger.error("Failed to download playlist content")
                return

            # Step 5: Start heartbeat loop
            logger.info("Starting main loop...")

            # Run playlist in separate thread
            import threading
            playlist_thread = threading.Thread(
                target=self.execute_playlist,
                args=(playlist_dict,),
                daemon=True,
            )
            playlist_thread.start()

            # Heartbeat loop in main thread
            while self._running:
                self.send_heartbeat()

                # Calculate sleep time (send heartbeat more frequently than interval)
                time.sleep(self.config.heartbeat_interval)

        except Exception as e:
            logger.error(f"Client error: {e}", exc_info=True)

        finally:
            self.shutdown()

    def stop(self) -> None:
        """Stop device client."""
        logger.info("Stopping device client...")
        self._running = False

    def shutdown(self) -> None:
        """Cleanup and shutdown."""
        logger.info("Shutting down...")

        if self.display:
            self.display.shutdown()

        if self.api_client:
            self.api_client.close()

        logger.info("Shutdown complete")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="HoloHub Device Client")
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file",
    )
    parser.add_argument(
        "--hardware-id",
        type=str,
        help="Device hardware ID (overrides config)",
    )
    parser.add_argument(
        "--device-secret",
        type=str,
        help="Device secret (overrides config)",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        help="Backend API URL (overrides config)",
    )
    parser.add_argument(
        "--simulation",
        action="store_true",
        default=True,
        help="Run in simulation mode (default)",
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Run in production mode (real display)",
    )
    parser.add_argument(
        "--real-3d",
        action="store_true",
        help="Run in real 3D mode (pyglet + trimesh window)",
    )

    args = parser.parse_args()

    # Load config
    client = DeviceClient(config_file=args.config, real_3d=args.real_3d)

    # Override with command line arguments
    if args.hardware_id:
        client.config.hardware_id = args.hardware_id
    if args.device_secret:
        client.config.device_secret = args.device_secret
    if args.api_url:
        client.config.api_base_url = args.api_url
    if args.production:
        client.config.simulation_mode = False

    # Start client
    client.start()


if __name__ == "__main__":
    main()
