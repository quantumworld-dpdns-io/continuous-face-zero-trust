"""Core authentication flow."""
from __future__ import annotations

import structlog
from app.config import settings
from app.core.token_service import TokenService
from app.core.risk_engine import RiskEngine
from app.core.face_verify import FaceVerifier
from app.core.liveness_check import LivenessChecker
from app.core.zk_verify import ZKVerifier

logger = structlog.get_logger()


class Authenticator:
    def __init__(self):
        self.token_service = TokenService()
        self.risk_engine = RiskEngine()
        self.face_verifier = FaceVerifier()
        self.liveness_checker = LivenessChecker()
        self.zk_verifier = ZKVerifier()

    async def authenticate(self, face_image: bytes, device_id: str, platform: str) -> dict:
        liveness = await self.liveness_checker.check(face_image)
        if not liveness["passed"]:
            logger.warning("Liveness check failed", device_id=device_id)
            return {"authenticated": False, "reason": "liveness_failed", "liveness": liveness}

        embedding = await self.face_verifier.generate_embedding(face_image)
        match_result = await self.face_verifier.verify_embedding(embedding, device_id)
        if not match_result["match"]:
            logger.warning("Face verification failed", device_id=device_id)
            return {"authenticated": False, "reason": "face_mismatch"}

        risk = self.risk_engine.score(device_id=device_id, platform=platform, liveness=liveness)

        zk_proof = await self.zk_verifier.generate_face_proof(embedding)

        token_pair = await self.token_service.create_pair(device_id=device_id, risk_score=risk["score"])

        logger.info("Authentication successful", device_id=device_id, risk_score=risk["score"])

        return {
            "authenticated": True,
            **token_pair,
            "risk_score": risk,
            "liveness": liveness,
            "zk_proof": zk_proof,
        }
