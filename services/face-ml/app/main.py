"""Face ML Service — face detection, embedding, liveness, quantum enhancement."""
from __future__ import annotations

from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI
from app.config import settings

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting face-ml service")
    yield
    logger.info("Shutting down face-ml service")


app = FastAPI(title="Face ML Service", version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "face-ml"}
