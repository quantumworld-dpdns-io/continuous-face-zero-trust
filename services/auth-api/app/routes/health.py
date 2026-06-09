"""Health check routes."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "service": "auth-api"}


@router.get("/ready")
async def ready():
    return {"status": "ready", "service": "auth-api"}
