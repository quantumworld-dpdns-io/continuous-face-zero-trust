"""Session management routes."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/{session_id}")
async def get_session(session_id: str):
    from app.dependencies import get_redis
    redis = await get_redis()
    session_data = await redis.hgetall(f"session:{session_id}")
    if not session_data:
        return {"error": "Session not found"}, 404
    return session_data


@router.delete("/{session_id}")
async def revoke_session(session_id: str, reason: str = "user_requested"):
    from app.dependencies import get_redis
    redis = await get_redis()
    await redis.delete(f"session:{session_id}")
    await redis.srem("active_sessions", session_id)
    return {"revoked": True, "session_id": session_id, "reason": reason}
