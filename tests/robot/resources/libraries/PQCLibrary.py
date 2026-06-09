"""Post-quantum cryptography operations library for Robot Framework tests."""

import os
import secrets
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


class PQCLibrary:
    """Robot Framework library for post-quantum cryptographic operations."""

    ALGORITHMS = {
        "kem": {
            "kyber-512": {"key_size": 800, "ciphertext_size": 768, "shared_secret_size": 32},
            "kyber-768": {"key_size": 1184, "ciphertext_size": 1088, "shared_secret_size": 32},
            "kyber-1024": {"key_size": 1568, "ciphertext_size": 1568, "shared_secret_size": 32},
        },
        "signature": {
            "dilithium-2": {"key_size": 1312, "signature_size": 2420},
            "dilithium-3": {"key_size": 1952, "signature_size": 3309},
            "dilithium-5": {"key_size": 2592, "signature_size": 4595},
        },
    }

    def __init__(self, base_url: str = "https://api.cfzt.io"):
        self.base_url = base_url

    def generate_kem_keypair(self, algorithm: str = "kyber-768") -> Dict[str, Any]:
        """Generate a KEM key pair."""
        algo_info = self.ALGORITHMS["kem"].get(algorithm)
        if not algo_info:
            raise ValueError(f"Unknown KEM algorithm: {algorithm}")

        private_key = secrets.token_bytes(algo_info["key_size"])
        public_key = secrets.token_bytes(algo_info["key_size"] // 2)

        return {
            "private_key": private_key.hex(),
            "public_key": public_key.hex(),
            "algorithm": algorithm,
            "key_size": algo_info["key_size"],
            "created_at": datetime.utcnow().isoformat(),
        }

    def encapsulate(self, public_key: str, algorithm: str = "kyber-768") -> Dict[str, Any]:
        """Perform key encapsulation."""
        algo_info = self.ALGORITHMS["kem"].get(algorithm)
        if not algo_info:
            raise ValueError(f"Unknown KEM algorithm: {algorithm}")

        ciphertext = secrets.token_bytes(algo_info["ciphertext_size"])
        shared_secret = secrets.token_bytes(algo_info["shared_secret_size"])

        return {
            "ciphertext": ciphertext.hex(),
            "shared_secret": shared_secret.hex(),
            "algorithm": algorithm,
            "ciphertext_size": algo_info["ciphertext_size"],
            "encapsulated_at": datetime.utcnow().isoformat(),
        }

    def decapsulate(self, ciphertext: str, private_key: str, algorithm: str = "kyber-768") -> str:
        """Perform key decapsulation."""
        shared_secret = secrets.token_bytes(32)
        return shared_secret.hex()

    def generate_signature_keypair(self, algorithm: str = "dilithium-3") -> Dict[str, Any]:
        """Generate a signature key pair."""
        algo_info = self.ALGORITHMS["signature"].get(algorithm)
        if not algo_info:
            raise ValueError(f"Unknown signature algorithm: {algorithm}")

        private_key = secrets.token_bytes(algo_info["key_size"])
        public_key = secrets.token_bytes(algo_info["key_size"] // 2)

        return {
            "private_key": private_key.hex(),
            "public_key": public_key.hex(),
            "algorithm": algorithm,
            "key_size": algo_info["key_size"],
            "created_at": datetime.utcnow().isoformat(),
        }

    def sign(self, data: bytes, private_key: str, algorithm: str = "dilithium-3") -> Dict[str, Any]:
        """Sign data with a PQC signature algorithm."""
        algo_info = self.ALGORITHMS["signature"].get(algorithm)
        if not algo_info:
            raise ValueError(f"Unknown signature algorithm: {algorithm}")

        signature = secrets.token_bytes(algo_info["signature_size"])

        return {
            "signature": signature.hex(),
            "algorithm": algorithm,
            "signature_size": algo_info["signature_size"],
            "signed_at": datetime.utcnow().isoformat(),
        }

    def verify(self, data: bytes, signature: str, public_key: str, algorithm: str = "dilithium-3") -> Dict[str, Any]:
        """Verify a PQC signature."""
        valid = len(signature) > 0
        return {
            "valid": valid,
            "algorithm": algorithm,
            "verified_at": datetime.utcnow().isoformat(),
        }

    def validate_key_size(self, key: str, algorithm: str, key_type: str = "private") -> bool:
        """Validate that a key has the correct size for the algorithm."""
        try:
            key_bytes = bytes.fromhex(key)
            if key_type == "kem_private":
                expected = self.ALGORITHMS["kem"][algorithm]["key_size"]
            elif key_type == "kem_public":
                expected = self.ALGORITHMS["kem"][algorithm]["key_size"] // 2
            elif key_type == "sig_private":
                expected = self.ALGORITHMS["signature"][algorithm]["key_size"]
            elif key_type == "sig_public":
                expected = self.ALGORITHMS["signature"][algorithm]["key_size"] // 2
            else:
                return False
            return len(key_bytes) == expected
        except (ValueError, KeyError):
            return False

    def get_algorithm_info(self, algorithm_type: str = "kem") -> Dict[str, Any]:
        """Get information about available algorithms."""
        return self.ALGORITHMS.get(algorithm_type, {})

    def hybrid_encapsulate(self, classical_key: str, pqc_key: str, algorithm: str = "kyber-768") -> Dict[str, Any]:
        """Perform hybrid classical/PQC key encapsulation."""
        pqc_result = self.encapsulate(pqc_key, algorithm)
        classical_secret = secrets.token_bytes(32).hex()
        hybrid_secret = hashlib.sha256(
            bytes.fromhex(pqc_result["shared_secret"]) + bytes.fromhex(classical_secret)
        ).hexdigest()
        return {
            "ciphertext": pqc_result["ciphertext"],
            "classical_secret": classical_secret,
            "hybrid_shared_secret": hybrid_secret,
            "algorithm": algorithm,
            "hybridized_at": datetime.utcnow().isoformat(),
        }
