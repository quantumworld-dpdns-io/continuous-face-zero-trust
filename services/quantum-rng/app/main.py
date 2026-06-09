"""Quantum RNG Service — quantum true random number generation."""
from __future__ import annotations

from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI
from app.config import settings

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting quantum-rng service", backend=settings.QUANTUM_BACKEND)
    yield
    logger.info("Shutting down quantum-rng service")


app = FastAPI(title="Quantum RNG Service", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "quantum-rng", "backend": settings.QUANTUM_BACKEND}
