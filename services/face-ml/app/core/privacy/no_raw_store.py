"""Privacy module — ensures no raw face images are stored."""
from __future__ import annotations

import hashlib
import numpy as np


class PrivacyGuard:
    """Ensures all privacy guarantees: embedding-only storage, no raw images."""

    @staticmethod
    def ensure_no_raw_storage(data: dict) -> dict:
        if "image" in data or "raw_image" in data:
            raise ValueError("Raw image storage is forbidden by privacy policy")
        return data

    @staticmethod
    def embedding_only(embedding: np.ndarray, metadata: dict | None = None) -> dict:
        result = {
            "embedding": embedding.tolist(),
            "dimension": len(embedding),
            "hash": hashlib.sha256(embedding.tobytes()).hexdigest(),
        }
        if metadata:
            result["metadata"] = metadata
        return result

    @staticmethod
    def apply_differential_privacy(embedding: np.ndarray, epsilon: float = 1.0) -> np.ndarray:
        sensitivity = 1.0 / len(embedding)
        noise_scale = sensitivity / epsilon
        noise = np.random.laplace(0, noise_scale, embedding.shape)
        return embedding + noise
