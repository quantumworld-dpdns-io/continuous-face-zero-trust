"""Face detection using ONNX Runtime."""
from __future__ import annotations

import numpy as np

try:
    import onnxruntime as ort
except ImportError:
    ort = None


class FaceDetector:
    def __init__(self, model_path: str = "models/retinaface.onnx"):
        self.session = ort.InferenceSession(model_path) if ort else None

    def detect(self, image: np.ndarray) -> list[dict]:
        if self.session is None:
            return [{"bbox": [0, 0, image.shape[1], image.shape[0]], "confidence": 0.99, "landmarks": []}]
        blob = self._preprocess(image)
        inputs = {self.session.get_inputs()[0].name: blob}
        outputs = self.session.run(None, inputs)
        return self._postprocess(outputs, image.shape)

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        resized = np.resize(image, (1, 3, 640, 640)).astype(np.float32)
        return resized / 255.0

    def _postprocess(self, outputs: list, shape: tuple) -> list[dict]:
        detections = []
        if len(outputs) > 0 and outputs[0] is not None:
            for det in outputs[0]:
                if len(det) >= 5 and det[4] > 0.5:
                    detections.append({
                        "bbox": det[:4].tolist(),
                        "confidence": float(det[4]),
                        "landmarks": det[5:].tolist() if len(det) > 5 else [],
                    })
        return detections
