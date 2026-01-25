"""
Model Loader

Load and prepare 3D models for holographic display.
Supports GLB/GLTF files commonly used for holographic content.
"""
import logging
from pathlib import Path
from typing import Optional, Tuple, Any
import numpy as np


logger = logging.getLogger(__name__)


class ModelLoader:
    """
    Load and process 3D models for display.

    Uses trimesh for GLB/GLTF loading which provides:
    - Mesh data (vertices, faces, normals)
    - Materials and textures
    - Scene graph hierarchy
    """

    def __init__(self):
        self._trimesh = None
        self._pyrender = None

        # Try to import trimesh for GLB loading
        try:
            import trimesh
            self._trimesh = trimesh
            logger.info("trimesh available for 3D model loading")
        except ImportError:
            logger.warning("trimesh not installed. Install with: pip install trimesh[easy]")

        # Try to import pyrender for visualization
        try:
            import pyrender
            self._pyrender = pyrender
            logger.info("pyrender available for 3D visualization")
        except ImportError:
            logger.debug("pyrender not installed (optional)")

    def load_glb_model(self, file_path: Path) -> Optional[Any]:
        """
        Load a GLB/GLTF 3D model.

        Args:
            file_path: Path to GLB file

        Returns:
            trimesh.Scene object or None
        """
        if self._trimesh is None:
            logger.error("trimesh not available, cannot load 3D models")
            return None

        if not file_path.exists():
            logger.error(f"Model file not found: {file_path}")
            return None

        try:
            # Load GLB file
            scene = self._trimesh.load(str(file_path), force_load_meshes=True)
            logger.info(f"Loaded model from {file_path}")
            logger.debug(f"  Geometry: {len(scene.geometry)} geometries")
            logger.debug(f"  Graph: {len(scene.graph.nodes)} nodes")
            return scene
        except Exception as e:
            logger.error(f"Failed to load model from {file_path}: {e}")
            return None

    def get_model_info(self, model: Any) -> dict:
        """
        Get information about the loaded model.

        Args:
            model: trimesh.Scene object

        Returns:
            Dictionary with model information
        """
        if model is None:
            return {}

        try:
            # Extract mesh information
            mesh_count = len(model.geometry)
            vertex_count = 0
            face_count = 0

            for geom in model.geometry.values():
                v = geom.vertices
                f = geom.faces
                vertex_count += len(v)
                if hasattr(f, 'shape'):
                    face_count += f.shape[0] if len(f.shape) == 1 else np.prod(f.shape[:-1])
                else:
                    face_count += len(f)

            # Extract metadata
            metadata = {}
            if hasattr(model, 'metadata') and model.metadata:
                metadata = dict(model.metadata)

            return {
                "mesh_count": mesh_count,
                "vertex_count": vertex_count,
                "face_count": face_count,
                "metadata": metadata,
            }
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {}

    def normalize_model(self, model: Any, target_size: float = 1.0) -> Any:
        """
        Normalize model to fit within a target bounding box.

        Args:
            model: trimesh.Scene object
            target_size: Target size for the largest dimension

        Returns:
            Normalized model
        """
        if model is None:
            return None

        try:
            # Get scene bounds
            bounds = model.bounds
            if bounds is None or bounds.is_empty:
                logger.warning("Model has no geometry to normalize")
                return model

            # Calculate scale factor
            extents = bounds.extents
            max_extent = max(extents)
            scale = target_size / max_extent if max_extent > 0 else 1.0

            # Apply scale to all meshes
            for geom in model.geometry.values():
                geom.apply_scale([scale, scale, scale])

            logger.debug(f"Normalized model with scale factor: {scale:.4f}")
            return model
        except Exception as e:
            logger.error(f"Failed to normalize model: {e}")
            return model

    def get_model_display_data(self, file_path: Path) -> Optional[Tuple[Any, dict]]:
        """
        Load and prepare model for display.

        Args:
            file_path: Path to GLB file

        Returns:
            Tuple of (model, info) or None
        """
        model = self.load_glb_model(file_path)
        if model is None:
            return None

        # Normalize to reasonable size
        model = self.normalize_model(model, target_size=0.8)

        info = self.get_model_info(model)
        return model, info

    def is_available(self) -> bool:
        """Check if 3D model loading is available."""
        return self._trimesh is not None
