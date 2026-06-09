"""CryptoLibrary — Robot Framework library for cryptographic operations."""
from __future__ import annotations

import hashlib
import hmac
import secrets
import json
from base64 import b64encode, b64decode


class CryptoLibrary:
    """Robot Framework library providing crypto operations for security tests."""

    def __init__(self):
        self._keys: dict[str, bytes] = {}

    def generate_random_bytes(self, num_bytes: int) -> str:
        return b64encode(secrets.token_bytes(num_bytes)).decode()

    def sha256_hash(self, data: str) -> str:
        return hashlib.sha256(data.encode()).hexdigest()

    def sha512_hash(self, data: str) -> str:
        return hashlib.sha512(data.encode()).hexdigest()

    def hmac_sha256(self, key: str, message: str) -> str:
        return hmac.new(key.encode(), message.encode(), hashlib.sha256).hexdigest()

    def verify_hmac(self, key: str, message: str, expected: str) -> bool:
        computed = hmac.new(key.encode(), message.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(computed, expected)

    def generate_key_pair_ed25519(self) -> dict:
        from cryptography.hazmat.primitives.asymmetric import ed25519
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return {
            "private_key": b64encode(private_key.private_bytes(
                encoding=__import__('cryptography.hazmat.primitives.serialization', fromlist=['Encoding']).Encoding.Raw,
                format=__import__('cryptography.hazmat.primitives.serialization', fromlist=['PrivateFormat']).PrivateFormat.Raw,
                encryption_algorithm=__import__('cryptography.hazmat.primitives.serialization', fromlist=['NoEncryption']).NoEncryption()
            )).decode(),
            "public_key": b64encode(public_key.public_bytes(
                encoding=__import__('cryptography.hazmat.primitives.serialization', fromlist=['Encoding']).Encoding.Raw,
                format=__import__('cryptography.hazmat.primitives.serialization', fromlist=['PublicFormat']).PublicFormat.Raw
            )).decode(),
        }

    def constant_time_compare(self, a: str, b: str) -> bool:
        return hmac.compare_digest(a.encode(), b.encode())

    def base64_encode(self, data: str) -> str:
        return b64encode(data.encode()).decode()

    def base64_decode(self, data: str) -> str:
        return b64decode(data.encode()).decode()

    def json_hash(self, data: dict) -> str:
        canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()
