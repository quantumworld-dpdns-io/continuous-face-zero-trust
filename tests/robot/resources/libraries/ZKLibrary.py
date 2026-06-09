"""ZKLibrary — Robot Framework library for zero-knowledge proof operations."""
from __future__ import annotations

import hashlib
import struct


class ZKLibrary:
    """Robot Framework library for ZK proof test operations."""

    def __init__(self):
        self._proofs: dict[str, dict] = {}

    def generate_mock_proof(self, circuit_id: str, public_inputs: str, private_inputs: str) -> dict:
        proof_hash = hashlib.sha256(f"{circuit_id}:{public_inputs}:{private_inputs}".encode()).hexdigest()
        vk_hash = hashlib.sha256(f"vk:{circuit_id}".encode()).hexdigest()
        proof = {
            "proof": proof_hash,
            "verification_key": vk_hash,
            "circuit_id": circuit_id,
            "prover_used": "groth16",
            "proving_time_ms": 150,
        }
        self._proofs[proof_hash] = proof
        return proof

    def verify_proof_format(self, proof_data: dict) -> dict:
        required_fields = ["proof", "verification_key", "circuit_id", "prover_used"]
        present = [f for f in required_fields if f in proof_data]
        missing = [f for f in required_fields if f not in proof_data]
        return {
            "valid_format": len(missing) == 0,
            "present_fields": present,
            "missing_fields": missing,
        }

    def verify_prover_type(self, proof_data: dict, expected_prover: str) -> bool:
        return proof_data.get("prover_used") == expected_prover

    def verify_proving_time(self, proof_data: dict, max_ms: int) -> dict:
        actual = proof_data.get("proving_time_ms", 0)
        return {
            "passed": actual <= max_ms,
            "actual_ms": actual,
            "max_ms": max_ms,
        }

    def generate_face_proof_request(self, embedding: list[float], range_margin: float = 0.1) -> dict:
        return {
            "embedding": embedding,
            "range_min": [max(0, e - range_margin) for e in embedding[:5]],
            "range_max": [min(1, e + range_margin) for e in embedding[:5]],
            "prover_type": "groth16",
        }

    def generate_liveness_proof_request(self, liveness_score: float, threshold: float = 0.85) -> dict:
        return {
            "liveness_score": liveness_score,
            "threshold": threshold,
            "prover_type": "plonk",
        }

    def aggregate_proofs(self, proofs: list[dict]) -> dict:
        combined = "".join(p.get("proof", "") for p in proofs)
        agg_hash = hashlib.sha256(combined.encode()).hexdigest()
        return {
            "aggregated_proof": agg_hash,
            "proof_count": len(proofs),
            "aggregation_time_ms": len(proofs) * 50,
        }
