"""Cryptographic utilities — hash, sign, verify, HMAC."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from base64 import urlsafe_b64decode, urlsafe_b64encode

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, padding, rsa
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def sha512(data: bytes) -> bytes:
    return hashlib.sha512(data).digest()


def blake3_hash(data: bytes) -> bytes:
    try:
        import blake3
        return blake3.blake3(data).digest()
    except ImportError:
        return hashlib.sha256(data).digest()


def hmac_sha256(key: bytes, message: bytes) -> bytes:
    return hmac.new(key, message, hashlib.sha256).digest()


def generate_random_bytes(n: int) -> bytes:
    return secrets.token_bytes(n)


def generate_random_string(n: int) -> str:
    return secrets.token_urlsafe(n)


def derive_key_hkdf(password: bytes, salt: bytes, info: bytes, length: int = 32) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=length, salt=salt, info=info).derive(password)


def derive_key_pbkdf2(password: bytes, salt: bytes, iterations: int = 100_000, length: int = 32) -> bytes:
    return PBKDF2HMAC(algorithm=hashes.SHA256(), length=length, salt=salt, iterations=iterations).derive(password)


def b64_encode(data: bytes) -> str:
    return urlsafe_b64encode(data).rstrip(b"=").decode()


def b64_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    s += "=" * padding
    return urlsafe_b64decode(s)


def constant_time_compare(a: bytes, b: bytes) -> bool:
    return hmac.compare_digest(a, b)


class Ed25519KeyPair:
    def __init__(self):
        self.private_key = ed25519.Ed25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()

    def sign(self, message: bytes) -> bytes:
        return self.private_key.sign(message)

    def verify(self, message: bytes, signature: bytes) -> bool:
        try:
            self.public_key.verify(signature, message)
            return True
        except Exception:
            return False

    def public_bytes(self) -> bytes:
        return self.public_key.public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )

    @classmethod
    def from_public_bytes(cls, data: bytes) -> "Ed25519KeyPair":
        raise NotImplementedError


class RSAKeyPair:
    def __init__(self, key_size: int = 2048):
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
        self.public_key = self.private_key.public_key()

    def sign(self, message: bytes) -> bytes:
        return self.private_key.sign(message, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())

    def verify(self, message: bytes, signature: bytes) -> bool:
        try:
            self.public_key.verify(signature, message, padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())
            return True
        except Exception:
            return False

    def public_bytes(self) -> bytes:
        return self.public_key.public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )
