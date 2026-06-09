"""Error hierarchy for cfzt services."""
from __future__ import annotations


class CFZTError(Exception):
    def __init__(self, message: str, code: str = "INTERNAL", status_code: int = 500, details: dict | None = None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        return {"error": {"code": self.code, "message": self.message, "details": self.details}}


class UnauthenticatedError(CFZTError):
    def __init__(self, message: str = "Authentication required", details: dict | None = None):
        super().__init__(message, code="UNAUTHENTICATED", status_code=401, details=details)


class UnauthorizedError(CFZTError):
    def __init__(self, message: str = "Insufficient permissions", details: dict | None = None):
        super().__init__(message, code="UNAUTHORIZED", status_code=403, details=details)


class NotFoundError(CFZTError):
    def __init__(self, message: str = "Resource not found", details: dict | None = None):
        super().__init__(message, code="NOT_FOUND", status_code=404, details=details)


class InvalidArgumentError(CFZTError):
    def __init__(self, message: str = "Invalid argument", details: dict | None = None):
        super().__init__(message, code="INVALID_ARGUMENT", status_code=400, details=details)


class RateLimitedError(CFZTError):
    def __init__(self, message: str = "Rate limit exceeded", details: dict | None = None):
        super().__init__(message, code="RATE_LIMITED", status_code=429, details=details)


class QuantumBackendError(CFZTError):
    def __init__(self, message: str = "Quantum backend unavailable", details: dict | None = None):
        super().__init__(message, code="QUANTUM_BACKEND_UNAVAILABLE", status_code=503, details=details)


class ZKProofError(CFZTError):
    def __init__(self, message: str = "ZK proof invalid", details: dict | None = None):
        super().__init__(message, code="ZK_PROOF_INVALID", status_code=400, details=details)


class PQCKeyError(CFZTError):
    def __init__(self, message: str = "PQC key operation failed", details: dict | None = None):
        super().__init__(message, code="PQC_KEY_ERROR", status_code=400, details=details)


class FaceNotDetectedError(CFZTError):
    def __init__(self, message: str = "No face detected in image", details: dict | None = None):
        super().__init__(message, code="FACE_NOT_DETECTED", status_code=400, details=details)


class LivenessFailedError(CFZTError):
    def __init__(self, message: str = "Liveness check failed", details: dict | None = None):
        super().__init__(message, code="LIVENESS_FAILED", status_code=400, details=details)


class EmbeddingMismatchError(CFZTError):
    def __init__(self, message: str = "Face embedding does not match", details: dict | None = None):
        super().__init__(message, code="EMBEDDING_MISMATCH", status_code=400, details=details)
