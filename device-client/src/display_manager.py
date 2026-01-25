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

# Optional OpenGL imports - only available if pyglet is installed
try:
    import pyglet
    # Use PyOpenGL for constants (more reliable)
    from OpenGL.GL import (
        GL_DEPTH_TEST, GL_LIGHTING, GL_LIGHT0, GL_COLOR_MATERIAL,
        GL_AMBIENT_AND_DIFFUSE, GL_FRONT_AND_BACK, GL_POSITION,
        GL_AMBIENT, GL_DIFFUSE, GL_PROJECTION, GL_MODELVIEW,
        GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT,
        GL_VERTEX_ARRAY, GL_NORMAL_ARRAY, GL_TRIANGLES, GL_UNSIGNED_INT,
        GL_TRUE, GL_FALSE, GL_FLOAT, GL_DOUBLE,
        glEnable, glDisable, glLightfv, glClearColor,
        glMatrixMode, glLoadIdentity, glRotatef,
        glEnableClientState, glDisableClientState,
        glVertexPointer, glNormalPointer, glDrawElements, glDrawArrays,
        glFlush, glClear,
    )
    from OpenGL.GLU import gluPerspective, gluLookAt
    PYGLET_AVAILABLE = True
except ImportError:
    PYGLET_AVAILABLE = False
    pyglet = None


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


class Real3DDisplayBackend(DisplayBackend):
    """
    Real 3D display backend using pyglet + trimesh.

    Displays 3D GLB models in a rotating view.
    Works without Looking Glass hardware for testing.
    """

    def __init__(self, config: DisplayConfig):
        self.config = config
        self.current_content: Optional[ContentItem] = None
        self._window = None
        self._viewer = None
        self._scene = None
        self._initialized = False
        self._rotation = 0.0

    def initialize(self) -> bool:
        """Initialize 3D display window."""
        try:
            import trimesh

            logger.info(f"Initializing 3D display: {self.config.display_type.value}")
            logger.info(f"  Resolution: {self.config.resolution[0]}x{self.config.resolution[1]}")

            # Try to create a simple viewer with pyglet
            try:
                if not PYGLET_AVAILABLE:
                    raise ImportError("pyglet not available")

                # Create window with OpenGL config for compatibility profile
                from pyglet.gl import Config
                config = Config(
                    double_buffer=True,
                    depth_size=24,
                    major_version=2,
                    minor_version=1,
                    forward_compatible=False,
                )

                window_width, window_height = self.config.resolution
                self._window = pyglet.window.Window(
                    width=window_width,
                    height=window_height,
                    caption="HoloHub 3D Display",
                    resizable=False,
                    config=config,
                )

                # Setup basic OpenGL state
                glEnable(GL_DEPTH_TEST)
                glClearColor(0.1, 0.1, 0.1, 1.0)

                # Set up the draw handler for rendering
                self._window.on_draw = self._render_scene

                self._initialized = True
                logger.info("3D display window initialized successfully")

            except ImportError:
                logger.warning("pyglet not available, using viewer mode")
                # Fall back to trimesh viewer if available
                self._use_viewer_mode()

            return True

        except ImportError:
            logger.error("Neither pyglet nor trimesh viewer available")
            return False

    def _use_viewer_mode(self) -> bool:
        """Use trimesh's built-in viewer."""
        if self._trimesh is None:
            return False

        logger.info("Using trimesh viewer mode")
        return True

    def show_content(self, content: ContentItem) -> bool:
        """Show 3D content on display."""
        if not self._initialized:
            logger.error("Display not initialized")
            return False

        if not content.file_path.exists():
            logger.error(f"Content file not found: {content.file_path}")
            return False

        try:
            import trimesh

            # Load the 3D model
            logger.info(f"Loading 3D model: {content.file_path}")
            scene = trimesh.load(str(content.file_path), force_load_meshes=True)

            # Center and scale the model
            scene = self._normalize_scene(scene)

            self._scene = scene
            self.current_content = content

            # The main loop handles rendering - no need to start separate event loop
            logger.info(f"Model loaded: {content.asset_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to display 3D content: {e}")
            return False

    def _normalize_scene(self, scene):
        """Center and scale scene for display."""
        import numpy as np
        import trimesh

        # Get scene bounds - returns numpy array with shape (2, 3)
        # bounds[0] is min, bounds[1] is max
        bounds = scene.bounds
        if bounds is not None and bounds.shape == (2, 3):
            # Calculate centroid (center of bounds)
            centroid = (bounds[0] + bounds[1]) / 2

            # Center the scene - apply_translation takes a translation vector
            translation = -centroid
            for geom in scene.geometry.values():
                geom.apply_translation(translation)

            # Scale to fit in view
            extents = bounds[1] - bounds[0]  # Size along each axis
            max_extent = float(np.max(extents))
            if max_extent > 0:
                scale = 1.5 / max_extent  # Make it fill about 75% of view
                for geom in scene.geometry.values():
                    geom.apply_scale([scale, scale, scale])

        return scene

    def _start_rendering(self, duration: Optional[int] = None):
        """
        Start the rendering loop for a specified duration.

        Args:
            duration: Duration in seconds to render. If None, runs indefinitely.
        """
        if not PYGLET_AVAILABLE:
            logger.error("pyglet not available for rendering")
            return

        if duration is None:
            # Run indefinitely
            pyglet.app.run()
        else:
            # Run for specified duration using clock tick
            import time as time_module
            start_time = time_module.time()

            def update(dt):
                elapsed = time_module.time() - start_time
                if elapsed >= duration:
                    pyglet.app.exit()

            # Schedule update and run
            pyglet.clock.schedule_interval(update, 0.1)
            pyglet.app.run()

    def _render_scene(self):
        """Render the current scene (called by pyglet)."""
        import trimesh
        import numpy as np

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self._scene is not None:
            # Set up simple camera
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            from pyglet.gl import gluPerspective
            gluPerspective(45, (self._window.width / self._window.height), 0.1, 100.0)

            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            from pyglet.gl import gluLookAt
            gluLookAt(0, 0, 3,  # Eye
                      0, 0, 0,   # Target
                      0, 1, 0)    # Up

            # Apply rotation
            glRotatef(self._rotation, 0, 1, 0)

            # Get geometry from scene
            for geom in self._scene.geometry.values():
                # Convert trimesh geometry to OpenGL format
                vertices = geom.vertices
                faces = geom.faces

                # Check if it has vertex colors, otherwise use white
                if hasattr(geom, 'visual') and hasattr(geom.visual, 'face_colors'):
                    colors = geom.visual.face_colors
                else:
                    # Default white color
                    colors = np.ones((len(faces), 4), dtype=np.float32)

                # Enable vertex arrays
                glEnableClientState(GL_VERTEX_ARRAY)
                glVertexPointer(3, GL_DOUBLE, vertices)

                if hasattr(faces, 'shape') and len(faces.shape) == 2:
                    # Draw faces
                    glDrawElements(GL_TRIANGLES, faces.size, GL_UNSIGNED_INT, faces)
                else:
                    # Simple triangles
                    glDrawArrays(GL_TRIANGLES, 0, vertices.shape[0])

                glDisableClientState(GL_VERTEX_ARRAY)

        self._rotation += 0.5

        glFlush()

    def clear(self) -> None:
        """Clear display."""
        self._scene = None
        self.current_content = None
        if self._window is not None and PYGLET_AVAILABLE:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def set_brightness(self, brightness: int) -> None:
        """Set display brightness (0-100)."""
        self.config.brightness = max(0, min(100, brightness))
        # Clear color brightness adjustment
        if self._initialized and self._window is not None:
            b = brightness / 100.0
            glClearColor(b * 0.1, b * 0.1, b * 0.1, 1.0)

    def shutdown(self) -> None:
        """Shutdown display."""
        if self._window is not None:
            if PYGLET_AVAILABLE:
                pyglet.app.exit()
        self._initialized = False
        self._scene = None
        self.current_content = None


class DisplayManager:
    """
    Main display manager for holographic content.

    Supports multiple display backends and content types.
    """

    def __init__(self, config: DisplayConfig, simulation_mode: bool = True, real_3d: bool = False):
        self.config = config
        self.simulation_mode = simulation_mode
        self.real_3d = real_3d
        self.backend: Optional[DisplayBackend] = None

    def initialize(self) -> bool:
        """Initialize display backend."""
        if self.real_3d:
            # Try real 3D display (pyglet + trimesh)
            self.backend = Real3DDisplayBackend(self.config)
        elif self.simulation_mode:
            self.backend = SimulationDisplayBackend(self.config)
        else:
            # Try Looking Glass SDK
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
