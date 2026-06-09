"""Face verification orchestrator."""
from __future__ import annotations

import structlog
import httpx

from app.config import settings

logger = structlog.get_logger()


class FaceVerifier:
    def __init__(self):
        self.face_ml_url = settings.FACE_ML_URL
        self.qdrant_url = settings.QDRANT_URL

    async def generate_embedding(self, face_image: bytes) -> list[float]:
        async with httpx.AsyncClient(base_url=self.face_ml_url, timeout=10.0) as client:
            resp = await client.post("/api/v1/face/embed", content=face_image, headers={"Content-Type": "image/jpeg"})
            resp.raise_for_status()
            data = resp.json()
            return data["embedding"]

    async def verify_embedding(self, embedding: list[float], device_id: str) -> dict:
        async with httpx.AsyncClient(base_url=self.face_ml_url, timeout=10.0) as client:
            resp = await client.post(
                "/api/v1/face/search",
                json={"embedding": embedding, "top_k": 1, "filters": {"device_id": device_id}},
            )
            resp.raise_for_status()
            data = resp.json()
            if data["results"]:
                best = data["results"][0]
                return {"match": best["score"] >= settings.FACE_MATCH_THRESHOLD, "score": best["score"]}
            return {"match": False, "score": 0.0}
