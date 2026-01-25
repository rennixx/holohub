"""
Device API Client

Handles communication between device and HoloHub backend.
"""
import os
import time
import json
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

import httpx


logger = logging.getLogger(__name__)


@dataclass
class AuthToken:
    """Authentication token for device."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 2592000  # 30 days
    device_id: str = ""
    organization_id: str = ""
    expires_at: float = 0

    def is_expired(self) -> bool:
        """Check if token is expired."""
        return time.time() > self.expires_at


class DeviceAPIClient:
    """
    API client for HoloHub device communication.

    Handles authentication, heartbeat, content fetching, and command reception.
    """

    def __init__(
        self,
        api_base_url: str,
        hardware_id: str,
        device_secret: str,
        timeout: int = 30,
    ):
        self.api_base_url = api_base_url.rstrip("/")
        self.hardware_id = hardware_id
        self.device_secret = device_secret
        self.timeout = timeout
        self._token: Optional[AuthToken] = None
        self._client = httpx.Client(timeout=timeout)

    @property
    def is_authenticated(self) -> bool:
        """Check if device is authenticated with valid token."""
        return self._token is not None and not self._token.is_expired()

    @property
    def auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        if not self.is_authenticated:
            return {}
        return {"Authorization": f"{self._token.token_type} {self._token.access_token}"}

    def authenticate(self) -> AuthToken:
        """
        Authenticate device with backend.

        Returns:
            AuthToken: Authentication token

        Raises:
            httpx.HTTPError: If authentication fails
        """
        logger.info(f"Authenticating device {self.hardware_id}...")

        response = self._client.post(
            f"{self.api_base_url}/api/v1/devices/auth",
            json={
                "hardware_id": self.hardware_id,
                "device_secret": self.device_secret,
            },
        )
        response.raise_for_status()

        data = response.json()
        self._token = AuthToken(
            access_token=data["access_token"],
            token_type=data.get("token_type", "bearer"),
            expires_in=data["expires_in"],
            device_id=data.get("device_id", ""),
            organization_id=data.get("organization_id", ""),
            expires_at=time.time() + data["expires_in"],
        )

        logger.info(f"Device authenticated: {self._token.device_id}")
        return self._token

    def ensure_authenticated(self) -> None:
        """Ensure device is authenticated, re-authenticate if needed."""
        if not self.is_authenticated:
            self.authenticate()

    def send_heartbeat(
        self,
        cpu_percent: Optional[float] = None,
        memory_percent: Optional[float] = None,
        storage_used_gb: Optional[float] = None,
        temperature_celsius: Optional[int] = None,
        bandwidth_mbps: Optional[int] = None,
        latency_ms: Optional[int] = None,
        current_playlist_id: Optional[str] = None,
        current_asset_id: Optional[str] = None,
        playback_position_sec: Optional[int] = None,
        firmware_version: Optional[str] = None,
        client_version: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send heartbeat to backend.

        Returns:
            Heartbeat response

        Raises:
            httpx.HTTPError: If heartbeat fails
        """
        self.ensure_authenticated()

        payload = {
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory_percent,
            "storage_used_gb": storage_used_gb,
            "temperature_celsius": temperature_celsius,
            "bandwidth_mbps": bandwidth_mbps,
            "latency_ms": latency_ms,
            "current_playlist_id": current_playlist_id,
            "current_asset_id": current_asset_id,
            "playback_position_sec": playback_position_sec,
            "firmware_version": firmware_version,
            "client_version": client_version,
        }

        # Remove None values
        payload = {k: v for k, v in payload.items() if v is not None}

        response = self._client.post(
            f"{self.api_base_url}/api/v1/devices/{self._token.device_id}/heartbeat",
            json=payload,
            headers=self.auth_headers,
        )
        response.raise_for_status()

        return response.json()

    def get_device_info(self) -> Dict[str, Any]:
        """
        Get device information from backend.

        Returns:
            Device information

        Raises:
            httpx.HTTPError: If request fails
        """
        self.ensure_authenticated()

        response = self._client.get(
            f"{self.api_base_url}/api/v1/devices/{self._token.device_id}",
            headers=self.auth_headers,
        )
        response.raise_for_status()

        return response.json()

    def get_assigned_playlist(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently assigned playlist for this device.

        Returns:
            Playlist data or None if no playlist assigned

        Raises:
            httpx.HTTPError: If request fails
        """
        self.ensure_authenticated()

        try:
            response = self._client.get(
                f"{self.api_base_url}/api/v1/devices/{self._token.device_id}/playlists",
                headers=self.auth_headers,
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.warning(f"Failed to get playlist: {e}")
            return None

    def get_content(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """
        Get content/asset information from backend.

        Args:
            asset_id: Asset ID to fetch

        Returns:
            Asset data or None if not found

        Raises:
            httpx.HTTPError: If request fails
        """
        self.ensure_authenticated()

        try:
            response = self._client.get(
                f"{self.api_base_url}/api/v1/assets/{asset_id}",
                headers=self.auth_headers,
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.warning(f"Failed to get asset {asset_id}: {e}")
            return None

    def download_content(
        self,
        file_path: str,
        destination: Path,
        progress_callback: Optional[callable] = None,
    ) -> Path:
        """
        Download content file from S3/storage.

        Args:
            file_path: S3 file path
            destination: Destination directory
            progress_callback: Optional callback for download progress

        Returns:
            Path to downloaded file

        Raises:
            httpx.HTTPError: If download fails
        """
        self.ensure_authenticated()

        # Get S3 endpoint and bucket from environment or device info
        device_info = self.get_device_info()
        # Assuming S3 URL format: {endpoint}/{bucket}/{file_path}
        # This would need to be adapted based on actual storage configuration

        url = f"{self.api_base_url}/api/v1/assets/download/{file_path}"

        destination.parent.mkdir(parents=True, exist_ok=True)

        with self._client.stream("GET", url, headers=self.auth_headers) as response:
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))

            with open(destination, "wb") as f:
                downloaded = 0
                for chunk in response.iter_bytes(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size > 0:
                        progress_callback(downloaded / total_size)

        logger.info(f"Downloaded content to {destination}")
        return destination

    def poll_commands(self, last_command_id: Optional[str] = None) -> list[Dict[str, Any]]:
        """
        Poll for pending commands from backend.

        Args:
            last_command_id: Last processed command ID

        Returns:
            List of pending commands

        Raises:
            httpx.HTTPError: If polling fails
        """
        self.ensure_authenticated()

        # This would be implemented when we add command queue functionality
        # For now, return empty list
        return []

    def report_command_result(
        self,
        command_id: str,
        success: bool,
        result: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Report command execution result to backend.

        Args:
            command_id: Command ID
            success: Whether command succeeded
            result: Optional result message
            error: Optional error message

        Raises:
            httpx.HTTPError: If report fails
        """
        self.ensure_authenticated()

        payload = {
            "command_id": command_id,
            "success": success,
            "result": result,
            "error": error,
        }

        response = self._client.post(
            f"{self.api_base_url}/api/v1/devices/{self._token.device_id}/commands/{command_id}/result",
            json=payload,
            headers=self.auth_headers,
        )
        response.raise_for_status()

        logger.info(f"Reported command result for {command_id}: {success}")

    def close(self) -> None:
        """Close the API client."""
        self._client.close()
