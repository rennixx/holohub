"""
Display Manager

Handles holographic display output.
Compatible with Looking Glass Factory displays.
Supports simulation mode for testing without hardware.
"""
import logging
import time
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


logger = logging.getLogger(__name__)


class DisplayType(Enum):
    """Supported display types."""

    LOOKING_GLASS_PORTRAIT = "looking_glass_portrait"
    LOOKING_GLASS_16 = "looking_glass_16"
    LOOKING_GLASS_32 = "looking_glass_32"
    LOOKING_GLASS_65 = "looking_glass_65"
    HYPERVSN_SOLO = "hypervsn_solo"
    WEB_EMULATOR = "web_emulator"


@dataclass
class DisplayConfig:
    """Display configuration."""

    display_type: DisplayType
    resolution: tuple[int, int] = (2048, 2048)
    quilt_views: int = 48
    quilt_depth: int = 45
    brightness: int = 80
    volume: int = 50
    orientation: str = "portrait"  # portrait or landscape


@dataclass
class ContentItem:
    """Content item for display."""

    asset_id: str
    file_path: Path
    content_type: str
    duration: Optional[int] = None  # Duration in seconds
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DisplayBackend(ABC):
    """Abstract base class for display backends."""

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize display. Return True if successful."""
        pass

    @abstractmethod
    def show_content(self, content: ContentItem) -> bool:
        """Show content on display. Return True if successful."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear display."""
        pass

    @abstractmethod
    def set_brightness(self, brightness: int) -> None:
        """Set display brightness (0-100)."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown display."""
        pass


class SimulationDisplayBackend(DisplayBackend):
    """
    Simulation display backend for testing without hardware.

    Logs what would be displayed on real hardware.
    """

    def __init__(self, config: DisplayConfig):
        self.config = config
        self.current_content: Optional[ContentItem] = None
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize simulation display."""
        logger.info(f"Initializing simulation display: {self.config.display_type.value}")
        logger.info(f"  Resolution: {self.config.resolution[0]}x{self.config.resolution[1]}")
        logger.info(f"  Quilt views: {self.config.quilt_views}, depth: {self.config.quilt_depth}")
        logger.info(f"  Brightness: {self.config.brightness}%")
        self._initialized = True
        return True

    def show_content(self, content: ContentItem) -> bool:
        """Simulate showing content."""
        if not self._initialized:
            logger.error("Display not initialized")
            return False

        logger.info("=" * 60)
        logger.info(f"DISPLAYING CONTENT: {content.asset_id}")
        logger.info(f"  File: {content.file_path}")
        logger.info(f"  Type: {content.content_type}")
        logger.info(f"  Duration: {content.duration or 'Loop'}")
        if content.metadata:
            logger.info(f"  Metadata: {content.metadata}")
        logger.info("=" * 60)

        self.current_content = content

        # Simulate display duration
        if content.duration:
            logger.info(f"  Displaying for {content.duration} seconds...")
            time.sleep(min(content.duration, 5))  # Max 5 seconds in sim mode
        else:
            logger.info(f"  Displaying (loop mode)...")

        return True

    def clear(self) -> None:
        """Clear display."""
        logger.info("Clearing display")
        self.current_content = None

    def set_brightness(self, brightness: int) -> None:
        """Set display brightness."""
        logger.info(f"Setting brightness to {brightness}%")
        self.config.brightness = max(0, min(100, brightness))

    def shutdown(self) -> None:
        """Shutdown display."""
        logger.info("Shutting down simulation display")
        self._initialized = False
        self.current_content = None


class LookingGlassDisplayBackend(DisplayBackend):
    """
    Real Looking Glass display backend using Looking Glass SDK.

    Requires:
    - Looking Glass SDK installed
    - Connected Looking Glass display
    - Supported content formats (GLB, quilt files)
    """

    def __init__(self, config: DisplayConfig):
        self.config = config
        self.current_content: Optional[ContentItem] = None
        self._display = None
        self._initialized = False

        # Try to import Looking Glass SDK
        try:
            from looking_glass import LookingGlassDisplay
            self._lg_sdk = LookingGlassDisplay
        except ImportError:
            logger.warning("Looking Glass SDK not installed. Install with: pip install lookingglass")
            self._lg_sdk = None

    def initialize(self) -> bool:
        """Initialize Looking Glass display."""
        if self._lg_sdk is None:
            logger.error("Looking Glass SDK not available")
            return False

        try:
            logger.info(f"Initializing Looking Glass display: {self.config.display_type.value}")
            self._display = self._lg_sdk(
                resolution=self.config.resolution,
                quilt_views=self.config.quilt_views,
                quilt_depth=self.config.quilt_depth,
            )
            self._display.initialize()
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Looking Glass display: {e}")
            return False

    def show_content(self, content: ContentItem) -> bool:
        """Show content on Looking Glass display."""
        if not self._initialized or self._display is None:
            logger.error("Display not initialized")
            return False

        try:
            # Check if file exists
            if not content.file_path.exists():
                logger.error(f"Content file not found: {content.file_path}")
                return False

            # Display based on content type
            if content.content_type == "model/glb":
                # Load and display GLB model
                self._display.load_model(str(content.file_path))
                self._display.render()

            elif content.content_type.startswith("quilt"):
                # Display quilt file (pre-rendered holographic image sequence)
                self._display.load_quilt(str(content.file_path))
                self._display.render()

            else:
                logger.warning(f"Unsupported content type: {content.content_type}")
                return False

            self.current_content = content
            logger.info(f"Displaying content: {content.asset_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to show content: {e}")
            return False

    def clear(self) -> None:
        """Clear display."""
        if self._display:
            self._display.clear()
        self.current_content = None

    def set_brightness(self, brightness: int) -> None:
        """Set display brightness."""
        if self._display:
            self._display.set_brightness(max(0, min(100, brightness)))
        self.config.brightness = max(0, min(100, brightness))

    def shutdown(self) -> None:
        """Shutdown display."""
        if self._display:
            self._display.shutdown()
        self._initialized = False
        self.current_content = None


class DisplayManager:
    """
    Main display manager for holographic content.

    Supports multiple display backends and content types.
    """

    def __init__(self, config: DisplayConfig, simulation_mode: bool = True):
        self.config = config
        self.simulation_mode = simulation_mode
        self.backend: Optional[DisplayBackend] = None

    def initialize(self) -> bool:
        """Initialize display backend."""
        if self.simulation_mode:
            self.backend = SimulationDisplayBackend(self.config)
        else:
            # Try real display backends
            self.backend = LookingGlassDisplayBackend(self.config)

        return self.backend.initialize()

    def show_asset(self, asset_id: str, file_path: Path, content_type: str, metadata: Optional[Dict] = None) -> bool:
        """
        Show asset on display.

        Args:
            asset_id: Asset ID
            file_path: Path to content file
            content_type: Content MIME type
            metadata: Optional asset metadata

        Returns:
            True if successful
        """
        content = ContentItem(
            asset_id=asset_id,
            file_path=file_path,
            content_type=content_type,
            duration=metadata.get("duration") if metadata else None,
            metadata=metadata or {},
        )
        return self.backend.show_content(content)

    def show_playlist_item(self, item: Dict[str, Any], content_manager) -> bool:
        """
        Show item from playlist.

        Args:
            item: Playlist item dictionary
            content_manager: ContentManager instance

        Returns:
            True if successful
        """
        asset_id = item.get("asset_id")
        if not asset_id:
            logger.error("Playlist item missing asset_id")
            return False

        # Get content from cache
        content_path = content_manager.get_content_for_display(asset_id)
        if not content_path:
            logger.error(f"Asset {asset_id} not cached")
            return False

        return self.show_asset(
            asset_id=asset_id,
            file_path=content_path,
            content_type=item.get("content_type", "model/glb"),
            metadata=item.get("metadata", {}),
        )

    def clear(self) -> None:
        """Clear display."""
        self.backend.clear()

    def set_brightness(self, brightness: int) -> None:
        """Set display brightness (0-100)."""
        self.backend.set_brightness(brightness)

    def shutdown(self) -> None:
        """Shutdown display."""
        self.backend.shutdown()
