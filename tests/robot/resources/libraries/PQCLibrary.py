"""PQCLibrary — Robot Framework library for post-quantum cryptography operations."""
from __future__ import annotations

import hashlib


class PQCLibrary:
    """Robot Framework library for PQC test operations."""

    ALGORITHMS = {
        "KYBER_512": {"type": "kem", "security_level": 1, "key_size": 800, "ciphertext_size": 768},
        "KYBER_768": {"type": "kem", "security_level": 3, "key_size": 1184, "ciphertext_size": 1088},
        "KYBER_1024": {"type": "kem", "security_level": 5, "key_size": 1568, "ciphertext_size": 1568},
        "DILITHIUM_2": {"type": "signature", "security_level": 2, "key_size": 1312, "signature_size": 2420},
        "DILITHIUM_3": {"type": "signature", "security_level": 3, "key_size": 1952, "signature_size": 3293},
        "DILITHIUM_5": {"type": "signature", "security_level": 5, "key_size": 2592, "signature_size": 4595},
        "FALCON_512": {"type": "signature", "security_level": 1, "key_size": 896, "signature_size": 666},
        "FALCON_1024": {"type": "signature", "security_level": 5, "key_size": 1792, "signature_size": 1280},
    }

    def __init__(self):
        self._key_pairs: dict[str, dict] = {}
        self._signatures: dict[str, bytes] = {}

    def get_algorithm_info(self, algorithm: str) -> dict:
        return self.ALGORITHMS.get(algorithm, {})

    def list_algorithms(self) -> list[str]:
        return list(self.ALGORITHMS.keys())

    def list_kem_algorithms(self) -> list[str]:
        return [k for k, v in self.ALGORITHMS.items() if v["type"] == "kem"]

    def list_signature_algorithms(self) -> list[str]:
        return [k for k, v in self.ALGORITHMS.items() if v["type"] == "signature"]

    def verify_key_size(self, algorithm: str, actual_key_size: int) -> dict:
        expected = self.ALGORITHMS.get(algorithm, {}).get("key_size", 0)
        return {
            "passed": actual_key_size == expected,
            "expected": expected,
            "actual": actual_key_size,
        }

    def verify_signature_size(self, algorithm: str, actual_sig_size: int) -> dict:
        expected = self.ALGORITHMS.get(algorithm, {}).get("signature_size", 0)
        return {
            "passed": actual_sig_size == expected,
            "expected": expected,
            "actual": actual_sig_size,
        }

    def generate_kem_test_vectors(self, algorithm: str) -> dict:
        info = self.ALGORITHMS.get(algorithm, {})
        key_hash = hashlib.sha256(f"pk:{algorithm}".encode()).hexdigest()
        ct_hash = hashlib.sha256(f"ct:{algorithm}".encode()).hexdigest()
        ss_hash = hashlib.sha256(f"ss:{algorithm}".encode()).hexdigest()
        return {
            "algorithm": algorithm,
            "public_key": key_hash,
            "ciphertext": ct_hash,
            "shared_secret": ss_hash,
            "key_size": info.get("key_size", 0),
            "ciphertext_size": info.get("ciphertext_size", 0),
        }

    def verify_hybrid_mode(self, classical_sig: str, pqc_sig: str) -> dict:
        return {
            "classical_present": bool(classical_sig),
            "pqc_present": bool(pqc_sig),
            "hybrid_valid": bool(classical_sig) and bool(pqc_sig),
        }
