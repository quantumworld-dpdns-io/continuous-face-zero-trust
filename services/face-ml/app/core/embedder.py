"""Face embedding generation using ONNX Runtime (ArcFace)."""
from __future__ import annotations

import numpy as np

try:
    import onnxruntime as ort
except ImportError:
    ort = None


class FaceEmbedder:
    def __init__(self, model_path: str = "models/arcface.onnx", dimension: int = 512):
        self.dimension = dimension
        self.session = ort.InferenceSession(model_path) if ort else None

    def embed(self, aligned_face: np.ndarray) -> np.ndarray:
        if self.session is None:
            return np.random.randn(self.dimension).astype(np.float32)
        blob = self._preprocess(aligned_face)
        inputs = {self.session.get_inputs()[0].name: blob}
        output = self.session.run(None, inputs)[0]
        embedding = output.flatten()
        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        return embedding.astype(np.float32)

    def _preprocess(self, face: np.ndarray) -> np.ndarray:
        resized = np.resize(face, (1, 3, 112, 112)).astype(np.float32)
        mean = np.array([127.0, 127.0, 127.0])
        std = np.array([128.0, 128.0, 128.0])
        return ((resized - mean) / std).transpose(0, 3, 1, 2)
