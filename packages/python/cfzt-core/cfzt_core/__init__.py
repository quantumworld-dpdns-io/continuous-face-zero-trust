"""cfzt-core — shared Python package for Continuous Face Zero Trust."""
__version__ = "0.1.0"

from cfzt_core.auth import TokenManager
from cfzt_core.crypto import sha256, hmac_sha256, generate_random_bytes
from cfzt_core.errors import CFZTError, UnauthenticatedError, NotFoundError
from cfzt_core.models import (
    AuthenticationResult,
    RiskScore,
    LivenessResult,
    ZKProofResult,
    HealthResponse,
)

__all__ = [
    "TokenManager",
    "sha256",
    "hmac_sha256",
    "generate_random_bytes",
    "CFZTError",
    "UnauthenticatedError",
    "NotFoundError",
    "AuthenticationResult",
    "RiskScore",
    "LivenessResult",
    "ZKProofResult",
    "HealthResponse",
]
