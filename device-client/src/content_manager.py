"""
Content Manager

Handles content downloading, caching, and management for holographic displays.
Compatible with Looking Glass Factory quilt formats and standard 3D formats.
"""
import os
import hashlib
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


@dataclass
class CachedContent:
    """Cached content metadata."""

    asset_id: str
    file_path: Path
    content_type: str
    file_size: int
    downloaded_at: datetime
    last_accessed: datetime
    checksum: str
    metadata: Dict[str, Any]


class ContentManager:
    """
    Manage content download, caching, and access.

    Supports:
    - GLB/GLTF files (3D models)
    - Quilt files (Looking Glass specific holographic format)
    - Images and videos
    """

    def __init__(self, cache_dir: Path, max_cache_size_gb: int = 10):
        self.cache_dir = cache_dir
        self.max_cache_size_gb = max_cache_size_gb
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        self.content_dir = self.cache_dir / "content"
        self.content_dir.mkdir(exist_ok=True)

        self.quilt_dir = self.cache_dir / "quilts"
        self.quilt_dir.mkdir(exist_ok=True)

        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata: Dict[str, CachedContent] = {}
        self._load_metadata()

    def _load_metadata(self) -> None:
        """Load cache metadata from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    data = json.load(f)
                    for asset_id, cached in data.items():
                        cached["downloaded_at"] = datetime.fromisoformat(cached["downloaded_at"])
                        cached["last_accessed"] = datetime.fromisoformat(cached["last_accessed"])
                        cached["file_path"] = Path(cached["file_path"])
                        self.metadata[asset_id] = CachedContent(**cached)
                logger.info(f"Loaded metadata for {len(self.metadata)} cached items")
            except Exception as e:
                logger.warning(f"Could not load cache metadata: {e}")

    def _save_metadata(self) -> None:
        """Save cache metadata to disk."""
        try:
            data = {}
            for asset_id, cached in self.metadata.items():
                data[asset_id] = {
                    "asset_id": cached.asset_id,
                    "file_path": str(cached.file_path),
                    "content_type": cached.content_type,
                    "file_size": cached.file_size,
                    "downloaded_at": cached.downloaded_at.isoformat(),
                    "last_accessed": cached.last_accessed.isoformat(),
                    "checksum": cached.checksum,
                    "metadata": cached.metadata,
                }
            with open(self.metadata_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save cache metadata: {e}")

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def get_cache_path(self, asset_id: str, content_type: str) -> Path:
        """
        Get cache file path for asset.

        Args:
            asset_id: Asset ID
            content_type: Content type (e.g., "model/glb", "quilt/png")

        Returns:
            Path where file should be cached
        """
        # Use content type subdirectory
        if content_type.startswith("quilt"):
            cache_subdir = self.quilt_dir
        else:
            cache_subdir = self.content_dir

        # Use asset_id as filename (with extension from content type)
        ext_map = {
            "model/glb": ".glb",
            "model/gltf": ".gltf",
            "quilt/png": ".png",
            "quilt/sequence": "_quilt.mp4",
        }
        ext = ext_map.get(content_type, ".bin")

        return cache_subdir / f"{asset_id}{ext}"

    def is_cached(self, asset_id: str) -> bool:
        """Check if asset is cached."""
        return asset_id in self.metadata and self.metadata[asset_id].file_path.exists()

    def get_cached(self, asset_id: str) -> Optional[CachedContent]:
        """Get cached content metadata."""
        if self.is_cached(asset_id):
            cached = self.metadata[asset_id]
            # Update last accessed time
            cached.last_accessed = datetime.now()
            self._save_metadata()
            return cached
        return None

    def cache_content(
        self,
        asset_id: str,
        source_path: Path,
        content_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CachedContent:
        """
        Cache content from source file.

        Args:
            asset_id: Asset ID
            source_path: Source file path
            content_type: Content type
            metadata: Optional metadata

        Returns:
            CachedContent metadata
        """
        cache_path = self.get_cache_path(asset_id, content_type)

        # Copy file to cache
        import shutil
        shutil.copy2(source_path, cache_path)

        # Create metadata
        cached = CachedContent(
            asset_id=asset_id,
            file_path=cache_path,
            content_type=content_type,
            file_size=cache_path.stat().st_size,
            downloaded_at=datetime.now(),
            last_accessed=datetime.now(),
            checksum=self._calculate_checksum(cache_path),
            metadata=metadata or {},
        )

        self.metadata[asset_id] = cached
        self._save_metadata()

        logger.info(f"Cached content {asset_id} to {cache_path}")
        return cached

    def download_content(
        self,
        api_client: "DeviceAPIClient",
        asset_id: str,
        asset_data: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[callable] = None,
    ) -> Optional[CachedContent]:
        """
        Download content from backend.

        Args:
            api_client: Device API client
            asset_id: Asset ID
            asset_data: Optional asset data from API
            progress_callback: Optional progress callback

        Returns:
            CachedContent if successful, None otherwise
        """
        # Get asset data if not provided
        if asset_data is None:
            asset_data = api_client.get_content(asset_id)
            if not asset_data:
                logger.error(f"Asset {asset_id} not found")
                return None

        content_type = asset_data.get("mime_type", "model/glb")
        cache_path = self.get_cache_path(asset_id, content_type)

        # Download file
        try:
            file_path = asset_data.get("file_path")
            if not file_path:
                logger.error(f"Asset {asset_id} has no file_path")
                return None

            api_client.download_content(
                file_path=file_path,
                destination=cache_path,
                progress_callback=progress_callback,
            )

            # Create cached metadata
            cached = CachedContent(
                asset_id=asset_id,
                file_path=cache_path,
                content_type=content_type,
                file_size=cache_path.stat().st_size,
                downloaded_at=datetime.now(),
                last_accessed=datetime.now(),
                checksum=self._calculate_checksum(cache_path),
                metadata=asset_data,
            )

            self.metadata[asset_id] = cached
            self._save_metadata()

            logger.info(f"Downloaded and cached asset {asset_id}")
            return cached

        except Exception as e:
            logger.error(f"Failed to download asset {asset_id}: {e}")
            return None

    def get_content_for_display(self, asset_id: str) -> Optional[Path]:
        """
        Get content file path for display.

        Args:
            asset_id: Asset ID

        Returns:
            Path to content file, or None if not available
        """
        cached = self.get_cached(asset_id)
        if cached:
            return cached.file_path
        return None

    def cleanup_old_content(self, max_age_days: int = 30) -> int:
        """
        Clean up old content from cache.

        Args:
            max_age_days: Maximum age in days

        Returns:
            Number of items cleaned up
        """
        cutoff = datetime.now() - timedelta(days=max_age_days)
        to_remove = []

        for asset_id, cached in self.metadata.items():
            if cached.last_accessed < cutoff:
                to_remove.append(asset_id)

        for asset_id in to_remove:
            self.remove_content(asset_id)

        logger.info(f"Cleaned up {len(to_remove)} old cache items")
        return len(to_remove)

    def remove_content(self, asset_id: str) -> bool:
        """
        Remove content from cache.

        Args:
            asset_id: Asset ID

        Returns:
            True if removed, False otherwise
        """
        if asset_id not in self.metadata:
            return False

        cached = self.metadata[asset_id]
        try:
            if cached.file_path.exists():
                cached.file_path.unlink()
            del self.metadata[asset_id]
            self._save_metadata()
            logger.info(f"Removed cached content {asset_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove cached content {asset_id}: {e}")
            return False

    def get_cache_size_gb(self) -> float:
        """
        Get current cache size in GB.

        Returns:
            Cache size in GB
        """
        total_size = 0
        for cached in self.metadata.values():
            if cached.file_path.exists():
                total_size += cached.file_path.stat().st_size
        return total_size / (1024**3)

    def enforce_cache_limit(self) -> None:
        """Enforce cache size limit by removing least recently used content."""
        cache_size = self.get_cache_size_gb()
        if cache_size <= self.max_cache_size_gb:
            return

        # Sort by last accessed time
        sorted_items = sorted(
            self.metadata.items(),
            key=lambda x: x[1].last_accessed,
        )

        # Remove oldest items until under limit
        removed = 0
        for asset_id, cached in sorted_items:
            if cache_size - (cached.file_size / (1024**3)) <= self.max_cache_size_gb:
                break
            if self.remove_content(asset_id):
                cache_size -= cached.file_size / (1024**3)
                removed += 1

        logger.info(f"Removed {removed} items to enforce cache limit")
