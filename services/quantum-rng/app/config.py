"""Quantum RNG configuration."""
from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "quantum-rng"
    QUANTUM_BACKEND: str = "local_simulator"
    IBM_QUANTUM_TOKEN: str = ""
    IBM_QUANTUM_INSTANCE: str = "ibm-q"
    MAX_QUBITS: int = 20
    ENTROPY_POOL_SIZE: int = 1024

    model_config = {"env_prefix": "CFZT_"}


settings = Settings()
