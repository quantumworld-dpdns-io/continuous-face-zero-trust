"""Liveness verification orchestrator."""
from __future__ import annotations

import structlog
import httpx

from app.config import settings

logger = structlog.get_logger()


class LivenessChecker:
    def __init__(self):
        self.face_ml_url = settings.FACE_ML_URL
        self.threshold = settings.LIVENESS_THRESHOLD

    async def check(self, face_image: bytes) -> dict:
        async with httpx.AsyncClient(base_url=self.face_ml_url, timeout=10.0) as client:
            resp = await client.post(
                "/api/v1/face/liveness",
                content=face_image,
                headers={"Content-Type": "image/jpeg"},
                params={"checks": "blink,depth,texture,anti_spoof"},
            )
            resp.raise_for_status()
            data = resp.json()

        passed = data["confidence"] >= self.threshold
        return {
            "passed": passed,
            "confidence": data["confidence"],
            "checks": data.get("check_scores", {}),
            "failed_checks": data.get("failed_checks", []),
        }
