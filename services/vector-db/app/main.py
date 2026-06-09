"""Vector DB Service — Qdrant operations."""
from __future__ import annotations

from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting vector-db service")
    yield
    logger.info("Shutting down vector-db service")


app = FastAPI(title="Vector DB Service", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "vector-db"}
