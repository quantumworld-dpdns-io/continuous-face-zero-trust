"""Token management routes."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    from app.core.token_service import TokenService
    ts = TokenService()
    try:
        result = await ts.refresh(refresh_token)
        return result
    except ValueError as e:
        return {"error": str(e)}, 401
