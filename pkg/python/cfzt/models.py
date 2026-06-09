"""Pydantic models for shared schemas."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    UNSPECIFIED = "UNSPECIFIED"
    UNAUTHENTICATED = "UNAUTHENTICATED"
    UNAUTHORIZED = "UNAUTHORIZED"
    NOT_FOUND = "NOT_FOUND"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL = "INTERNAL"
    UNAVAILABLE = "UNAVAILABLE"
    QUANTUM_BACKEND_UNAVAILABLE = "QUANTUM_BACKEND_UNAVAILABLE"
    ZK_PROOF_INVALID = "ZK_PROOF_INVALID"
    PQC_KEY_ERROR = "PQC_KEY_ERROR"
    FACE_NOT_DETECTED = "FACE_NOT_DETECTED"
    LIVENESS_FAILED = "LIVENESS_FAILED"
    EMBEDDING_MISMATCH = "EMBEDDING_MISMATCH"


class ErrorDetail(BaseModel):
    code: ErrorCode
    message: str
    metadata: dict[str, str] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorDetail


class PaginationRequest(BaseModel):
    cursor: str | None = None
    page_size: int = 20


class PaginationResponse(BaseModel):
    next_cursor: str | None = None
    has_more: bool = False
    total_count: int = 0


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskScore(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    level: RiskLevel
    factors: list[str] = Field(default_factory=list)


class LivenessResult(BaseModel):
    passed: bool
    confidence: float
    check_scores: dict[str, float] = Field(default_factory=dict)
    failed_checks: list[str] = Field(default_factory=list)
    checked_at: datetime | None = None


class ZKProofResult(BaseModel):
    valid: bool
    proof: str | None = None
    verification_key: str | None = None
    circuit_id: str | None = None


class AuthenticationResult(BaseModel):
    authenticated: bool
    session_token: str | None = None
    refresh_token: str | None = None
    expires_at: str | None = None
    session_id: str | None = None
    risk_score: RiskScore | None = None
    liveness: LivenessResult | None = None
    zk_proof: ZKProofResult | None = None
    reason: str | None = None


class SessionData(BaseModel):
    session_id: str
    user_id: str
    device_id: str
    platform: str
    created_at: datetime
    last_active: datetime
    risk_score: float
    active: bool = True


class FaceEmbedding(BaseModel):
    embedding: list[float]
    dimension: int
    model_version: str | None = None
    generated_at: datetime | None = None


class QuantumRNGResponse(BaseModel):
    random_bytes: str
    num_bits: int
    backend_used: str
    min_entropy: float
    nist_test_passed: bool


class PQCAlgorithmInfo(BaseModel):
    name: str
    category: str
    security_level: int
    key_size_bytes: int
    ciphertext_size_bytes: int


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str = "0.1.0"
    uptime_seconds: float | None = None


class MetricsResponse(BaseModel):
    total_authentications: int = 0
    successful_authentications: int = 0
    failed_authentications: int = 0
    active_sessions: int = 0
    avg_latency_ms: float = 0.0
