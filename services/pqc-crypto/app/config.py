"""PQC Crypto configuration."""
from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "pqc-crypto"
    PQC_ALGORITHMS: str = "kyber,dilithium,falcon"
    ENABLE_HYBRID: bool = True
    KEY_ROTATION_HOURS: int = 24

    model_config = {"env_prefix": "CFZT_"}


settings = Settings()
