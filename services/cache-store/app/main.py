"""Cache Store Service — Redis/DragonflyDB operations."""
from __future__ import annotations

from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting cache-store service")
    yield
    logger.info("Shutting down cache-store service")


app = FastAPI(title="Cache Store Service", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "cache-store"}
