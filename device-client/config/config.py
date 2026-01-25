"""
Device Client Configuration

Configuration for HoloHub device client.
Compatible with Looking Glass Factory holographic displays.
"""
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DeviceConfig:
    """Device client configuration."""

    # Server Configuration
    api_base_url: str = field(default_factory=lambda: os.getenv(
        "HOLOHUB_API_URL", "http://localhost:8000"
    ))
    api_timeout: int = field(default_factory=lambda: int(os.getenv("API_TIMEOUT", "30")))

    # Device Credentials (loaded from config file or environment)
    hardware_id: Optional[str] = field(default_factory=lambda: os.getenv("DEVICE_HARDWARE_ID"))
    device_secret: Optional[str] = field(default_factory=lambda: os.getenv("DEVICE_SECRET"))

    # Device Information
    device_name: str = "HoloHub Display"
    firmware_version: str = "1.0.0"
    client_version: str = "1.0.0"

    # Heartbeat Configuration
    heartbeat_interval: int = field(default_factory=lambda: int(os.getenv("HEARTBEAT_INTERVAL", "30")))
    heartbeat_timeout: int = field(default_factory=lambda: int(os.getenv("HEARTBEAT_TIMEOUT", "90")))

    # Content Configuration
    content_cache_dir: Path = field(default_factory=lambda: Path(
        os.getenv("CONTENT_CACHE_DIR", "./cache/content")
    ))
    max_cache_size_gb: int = field(default_factory=lambda: int(os.getenv("MAX_CACHE_SIZE_GB", "10")))

    # Display Configuration
    display_type: str = field(default_factory=lambda: os.getenv(
        "DISPLAY_TYPE", "looking_glass_portrait"
    ))

    # Resolution and quilt settings (Looking Glass specific)
    display_resolution: tuple[int, int] = field(default_factory=lambda: (
        int(os.getenv("DISPLAY_WIDTH", "2048")),
        int(os.getenv("DISPLAY_HEIGHT", "2048"))
    ))

    # Quilt settings (for holographic rendering)
    quilt_views: int = field(default_factory=lambda: int(os.getenv("QUILT_VIEWS", "48")))
    quilt_depth: int = field(default_factory=lambda: int(os.getenv("QUILT_DEPTH", "45")))

    # Simulation Mode
    simulation_mode: bool = field(default_factory=lambda: os.getenv(
        "SIMULATION_MODE", "true"
    ).lower() == "true")

    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_file: Optional[Path] = field(default_factory=lambda: Path(
        os.getenv("LOG_FILE")
    ) if os.getenv("LOG_FILE") else None)

    def __post_init__(self):
        """Create cache directory if it doesn't exist."""
        self.content_cache_dir.mkdir(parents=True, exist_ok=True)


def load_config(config_file: Optional[Path] = None) -> DeviceConfig:
    """
    Load device configuration from file or environment variables.

    Args:
        config_file: Optional path to configuration file

    Returns:
        DeviceConfig instance
    """
    config = DeviceConfig()

    if config_file and config_file.exists():
        # Load from file (simple key=value format)
        with open(config_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip().upper()
                    value = value.strip()

                    # Map config file keys to dataclass fields
                    if key == "API_BASE_URL":
                        config.api_base_url = value
                    elif key == "DEVICE_HARDWARE_ID":
                        config.hardware_id = value
                    elif key == "DEVICE_SECRET":
                        config.device_secret = value
                    elif key == "HEARTBEAT_INTERVAL":
                        config.heartbeat_interval = int(value)
                    elif key == "DISPLAY_TYPE":
                        config.display_type = value
                    elif key == "SIMULATION_MODE":
                        config.simulation_mode = value.lower() in ("true", "1", "yes")

    return config


# Display Type Constants (Looking Glass Factory compatible)
DISPLAY_TYPES = {
    "looking_glass_portrait": {
        "name": "Looking Glass Portrait",
        "resolution": (2048, 2048),
        "quilt_views": 48,
        "quilt_depth": 45,
        "diagonal_inches": 7.9,
    },
    "looking_glass_16": {
        "name": "Looking Glass 16 inch",
        "resolution": (4096, 4096),
        "quilt_views": 48,
        "quilt_depth": 45,
        "diagonal_inches": 16.0,
    },
    "looking_glass_32": {
        "name": "Looking Glass 32 inch",
        "resolution": (8192, 8192),
        "quilt_views": 48,
        "quilt_depth": 45,
        "diagonal_inches": 32.0,
    },
    "looking_glass_65": {
        "name": "Looking Glass 65 inch",
        "resolution": (8192, 8192),
        "quilt_views": 48,
        "quilt_depth": 45,
        "diagonal_inches": 65.0,
    },
    "hypervsn_solo": {
        "name": "Hypervsn Solo",
        "resolution": (1920, 1080),
        "quilt_views": None,  # LED fan displays use different rendering
        "quilt_depth": None,
        "diagonal_inches": 21.5,
    },
}

# Hardware Type Mapping to Backend
HARDWARE_TYPE_MAP = {
    "looking_glass_portrait": "looking_glass_portrait",
    "looking_glass_16": "looking_glass_16",
    "looking_glass_32": "looking_glass_32",
    "looking_glass_65": "looking_glass_65",
    "hypervsn_solo": "hypervsn_solo",
    "web_emulator": "web_emulator",
}
