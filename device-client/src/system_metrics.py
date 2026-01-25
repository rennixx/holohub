"""
System Metrics Collector

Collects system health metrics for device heartbeat.
Compatible with Raspberry Pi, Linux systems, and Windows.
"""
import platform
import logging
import subprocess
import time
from typing import Optional
from pathlib import Path


logger = logging.getLogger(__name__)


class SystemMetrics:
    """
    Collect system health metrics.

    Works on:
    - Raspberry Pi (Linux)
    - Linux systems
    - Windows (fallback/mode)
    """

    def __init__(self):
        self.system = platform.system().lower()
        self.is_raspberry_pi = self._detect_raspberry_pi()

    def _detect_raspberry_pi(self) -> bool:
        """Detect if running on Raspberry Pi."""
        try:
            if Path("/proc/device-tree/model").exists():
                with open("/proc/device-tree/model", "r") as f:
                    return "raspberry pi" in f.read().lower()
        except Exception:
            pass
        return False

    def get_cpu_percent(self) -> Optional[float]:
        """
        Get CPU usage percentage.

        Returns:
            CPU usage as percentage (0-100) or None if unavailable
        """
        try:
            if self.system in ("linux", "darwin"):
                # Use top for Linux/macOS
                result = subprocess.run(
                    ["top", "-bn1"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                for line in result.stdout.split("\n"):
                    if "Cpu(s)" in line or "%Cpu(s)" in line:
                        # Extract idle percentage
                        parts = line.split()
                        for i, part in enumerate(parts):
                            if "id" in part or part.endswith("%"):
                                try:
                                    idle = float(part.strip("%"))
                                    return 100.0 - idle
                                except ValueError:
                                    continue
                return None
            elif self.system == "windows":
                # Use wmic for Windows
                result = subprocess.run(
                    ["wmic", "cpu", "get", "loadpercentage", "/value"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                for line in result.stdout.split("\n"):
                    if "LoadPercentage" in line:
                        value = line.split("=")[1].strip()
                        return float(value)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.debug(f"Could not get CPU usage: {e}")

        # Fallback: use psutil if available
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            pass

        return None

    def get_memory_percent(self) -> Optional[float]:
        """
        Get memory usage percentage.

        Returns:
            Memory usage as percentage (0-100) or None if unavailable
        """
        try:
            # Try psutil first (works on all platforms)
            import psutil
            return psutil.virtual_memory().percent
        except ImportError:
            pass

        # Fallback to platform-specific methods
        try:
            if self.system == "linux":
                result = subprocess.run(
                    ["free", "-m"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                for line in result.stdout.split("\n"):
                    if "Mem:" in line:
                        parts = line.split()
                        total = float(parts[1])
                        used = float(parts[2])
                        return (used / total) * 100
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.debug(f"Could not get memory usage: {e}")

        return None

    def get_storage_used_gb(self) -> Optional[float]:
        """
        Get storage used in GB.

        Returns:
            Storage used in GB or None if unavailable
        """
        try:
            import psutil
            usage = psutil.disk_usage("/")
            return usage.used / (1024**3)  # Convert to GB
        except ImportError:
            pass

        try:
            if self.system == "linux":
                result = subprocess.run(
                    ["df", "-h", "/"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                for line in result.stdout.split("\n"):
                    if line.startswith("/dev/"):
                        parts = line.split()
                        if len(parts) >= 4:
                            used_str = parts[2]
                            if used_str.endswith("G"):
                                return float(used_str.rstrip("G"))
                            elif used_str.endswith("M"):
                                return float(used_str.rstrip("M")) / 1024
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.debug(f"Could not get storage usage: {e}")

        return None

    def get_temperature_celsius(self) -> Optional[int]:
        """
        Get CPU temperature in Celsius.

        Returns:
            Temperature in Celsius or None if unavailable
        """
        if self.is_raspberry_pi:
            try:
                # Raspberry Pi specific
                with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                    temp_millidegrees = int(f.read().strip())
                    return temp_millidegrees // 1000
            except (IOError, ValueError) as e:
                logger.debug(f"Could not get RPi temperature: {e}")

        try:
            import psutil
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    # Get first available temperature
                    for name, entries in temps.items():
                        if entries:
                            return int(entries[0].current)
        except ImportError:
            pass

        return None

    def get_network_latency_ms(self, api_base_url: str) -> Optional[int]:
        """
        Get network latency to backend server in milliseconds.

        Args:
            api_base_url: Backend server URL

        Returns:
            Latency in ms or None if unavailable
        """
        try:
            import httpx
            start = time.time()
            response = httpx.get(
                f"{api_base_url.rstrip('/')}/health",
                timeout=5,
            )
            response.raise_for_status()
            latency_ms = int((time.time() - start) * 1000)
            return latency_ms
        except Exception as e:
            logger.debug(f"Could not measure latency: {e}")
            return None

    def get_bandwidth_mbps(self) -> Optional[int]:
        """
        Get network bandwidth in Mbps (placeholder).

        Real implementation would measure actual network throughput.

        Returns:
            Bandwidth in Mbps or None if unavailable
        """
        # This would require actual network interface monitoring
        # For now, return None or a simulated value
        return None

    def get_all_metrics(self, api_base_url: Optional[str] = None) -> dict:
        """
        Get all available system metrics.

        Args:
            api_base_url: Optional backend URL for latency check

        Returns:
            Dictionary of metrics
        """
        metrics = {
            "cpu_usage_percent": self.get_cpu_percent(),
            "memory_usage_percent": self.get_memory_percent(),
            "storage_used_gb": self.get_storage_used_gb(),
            "temperature_celsius": self.get_temperature_celsius(),
            "bandwidth_mbps": self.get_bandwidth_mbps(),
        }

        if api_base_url:
            metrics["latency_ms"] = self.get_network_latency_ms(api_base_url)

        # Remove None values
        return {k: v for k, v in metrics.items() if v is not None}

    def get_device_info(self) -> dict:
        """
        Get device hardware information.

        Returns:
            Device information dictionary
        """
        info = {
            "platform": platform.platform(),
            "system": self.system,
            "machine": platform.machine(),
            "processor": platform.processor(),
            "is_raspberry_pi": self.is_raspberry_pi,
        }

        # Get Raspberry Pi specific info
        if self.is_raspberry_pi:
            try:
                # Get CPU info
                with open("/proc/cpuinfo", "r") as f:
                    cpuinfo = f.read()
                    for line in cpuinfo.split("\n"):
                        if line.startswith("Hardware"):
                            info["hardware"] = line.split(":", 1)[1].strip()
                        elif line.startswith("Revision"):
                            info["revision"] = line.split(":", 1)[1].strip()
            except IOError:
                pass

        return info


# Singleton instance
_metrics_instance: Optional[SystemMetrics] = None


def get_system_metrics() -> SystemMetrics:
    """Get or create system metrics singleton."""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = SystemMetrics()
    return _metrics_instance
