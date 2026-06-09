"""PQC Crypto Service — post-quantum cryptography operations."""
from __future__ import annotations

from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI
from app.config import settings

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting pqc-crypto service", algorithms=settings.PQC_ALGORITHMS)
    yield
    logger.info("Shutting down pqc-crypto service")


app = FastAPI(title="PQC Crypto Service", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "pqc-crypto"}
