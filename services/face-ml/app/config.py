"""Face ML configuration."""
from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "face-ml"
    MODEL_PATH: str = "./models"
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "face_embeddings"
    EMBEDDING_DIMENSION: int = 512
    FACE_MATCH_THRESHOLD: float = 0.72
    LIVENESS_THRESHOLD: float = 0.85
    DEVICE: str = "cpu"

    model_config = {"env_prefix": "CFZT_"}


settings = Settings()
