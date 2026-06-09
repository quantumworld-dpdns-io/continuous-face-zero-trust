"""Auth API configuration."""
from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "auth-api"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    REDIS_URL: str = "redis://localhost:6379"
    QDRANT_URL: str = "http://localhost:6333"
    FACE_ML_URL: str = "http://localhost:8001"
    ZK_PROOFS_URL: str = "http://localhost:8002"
    QUANTUM_RNG_URL: str = "http://localhost:8003"
    PQC_CRYPTO_URL: str = "http://localhost:8006"

    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 15
    REFRESH_EXPIRY_DAYS: int = 7

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    LIVENESS_THRESHOLD: float = 0.85
    FACE_MATCH_THRESHOLD: float = 0.72
    CONTINUOUS_VERIFY_INTERVAL_SECONDS: int = 30

    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"
    OTEL_SERVICE_NAME: str = "auth-api"

    RATE_LIMIT_PER_MINUTE: int = 60

    model_config = {"env_prefix": "CFZT_"}


settings = Settings()
