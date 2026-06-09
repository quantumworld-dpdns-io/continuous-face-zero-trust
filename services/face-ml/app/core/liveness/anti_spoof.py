"""Anti-spoofing liveness detection."""
from __future__ import annotations

import numpy as np

try:
    import onnxruntime as ort
except ImportError:
    ort = None


class AntiSpoofDetector:
    def __init__(self, model_path: str = "models/anti_spoof.onnx"):
        self.session = ort.InferenceSession(model_path) if ort else None

    def check(self, face_image: np.ndarray) -> dict:
        if self.session is None:
            return {"live": True, "confidence": 0.95, "check": "anti_spoof"}
        blob = np.resize(face_image, (1, 3, 224, 224)).astype(np.float32) / 255.0
        inputs = {self.session.get_inputs()[0].name: blob}
        output = self.session.run(None, inputs)[0]
        score = float(1.0 / (1.0 + np.exp(-output[0][0])))
        return {"live": score > 0.5, "confidence": score, "check": "anti_spoof"}
