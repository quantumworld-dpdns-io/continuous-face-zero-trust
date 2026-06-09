"""ZK proof verification orchestrator."""
from __future__ import annotations

import structlog
import httpx

from app.config import settings

logger = structlog.get_logger()


class ZKVerifier:
    def __init__(self):
        self.zk_url = settings.ZK_PROOFS_URL

    async def generate_face_proof(self, embedding: list[float]) -> dict:
        async with httpx.AsyncClient(base_url=self.zk_url, timeout=10.0) as client:
            resp = await client.post(
                "/api/v1/zk/face-proof",
                json={
                    "embedding": embedding,
                    "range_min": [max(0, e - 0.1) for e in embedding[:5]],
                    "range_max": [min(1, e + 0.1) for e in embedding[:5]],
                    "prover_type": "groth16",
                },
            )
            resp.raise_for_status()
            return resp.json()

    async def generate_liveness_proof(self, liveness_score: float) -> dict:
        async with httpx.AsyncClient(base_url=self.zk_url, timeout=10.0) as client:
            resp = await client.post(
                "/api/v1/zk/liveness-proof",
                json={"liveness_score": liveness_score, "threshold": settings.LIVENESS_THRESHOLD, "prover_type": "plonk"},
            )
            resp.raise_for_status()
            return resp.json()

    async def verify(self, proof: bytes, public_inputs: bytes, verification_key: bytes, circuit_id: str) -> bool:
        async with httpx.AsyncClient(base_url=self.zk_url, timeout=10.0) as client:
            resp = await client.post(
                "/api/v1/zk/verify",
                json={"proof": proof.hex(), "public_inputs": public_inputs.hex(), "verification_key": verification_key.hex(), "circuit_id": circuit_id},
            )
            resp.raise_for_status()
            return resp.json()["valid"]
