"""FaceMLLibrary — Robot Framework library for face ML operations."""
from __future__ import annotations

import hashlib
import numpy as np


class FaceMLLibrary:
    """Robot Framework library for face ML test operations."""

    def __init__(self):
        self._embeddings: dict[str, list[float]] = {}

    def generate_mock_embedding(self, seed: int = 42) -> list[float]:
        rng = np.random.RandomState(seed)
        embedding = rng.randn(512).astype(np.float32)
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        return embedding.tolist()

    def cosine_similarity(self, a: list[float], b: list[float]) -> float:
        a_arr = np.array(a)
        b_arr = np.array(b)
        return float(np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr) + 1e-8))

    def verify_match(self, similarity: float, threshold: float = 0.72) -> dict:
        return {
            "match": similarity >= threshold,
            "similarity": similarity,
            "threshold": threshold,
            "margin": similarity - threshold,
        }

    def detect_liveness_score(self, checks: dict[str, float]) -> dict:
        weights = {"anti_spoof": 0.4, "depth": 0.3, "texture": 0.3}
        weighted = sum(checks.get(k, 0) * weights.get(k, 0.33) for k in checks)
        return {
            "passed": weighted > 0.85,
            "confidence": weighted,
            "check_scores": checks,
        }

    def verify_privacy(self, data: dict) -> dict:
        has_raw = "image" in data or "raw_image" in data or "photo" in data
        has_embedding = "embedding" in data
        return {
            "no_raw_image": not has_raw,
            "has_embedding": has_embedding,
            "privacy_compliant": not has_raw and has_embedding,
        }

    def embedding_hash(self, embedding: list[float]) -> str:
        data = np.array(embedding).tobytes()
        return hashlib.sha256(data).hexdigest()

    def verify_embedding_dimension(self, embedding: list[float], expected_dim: int = 512) -> dict:
        actual_dim = len(embedding)
        return {
            "correct": actual_dim == expected_dim,
            "actual": actual_dim,
            "expected": expected_dim,
        }
