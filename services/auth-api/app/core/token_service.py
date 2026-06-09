"""Token service — JWT/PASETO generation and management."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt

from app.config import settings


class TokenService:
    async def create_pair(self, device_id: str, risk_score: float) -> dict:
        now = datetime.now(timezone.utc)
        session_id = str(uuid.uuid4())

        access_payload = {
            "sub": device_id,
            "sid": session_id,
            "iat": now,
            "exp": now + timedelta(minutes=settings.JWT_EXPIRY_MINUTES),
            "risk": risk_score,
            "type": "access",
        }
        refresh_payload = {
            "sub": device_id,
            "sid": session_id,
            "iat": now,
            "exp": now + timedelta(days=settings.REFRESH_EXPIRY_DAYS),
            "type": "refresh",
        }

        access_token = jwt.encode(access_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        refresh_token = jwt.encode(refresh_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

        return {
            "session_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": (now + timedelta(minutes=settings.JWT_EXPIRY_MINUTES)).isoformat(),
            "session_id": session_id,
        }

    async def refresh(self, refresh_token: str) -> dict:
        payload = jwt.decode(refresh_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        return await self.create_pair(device_id=payload["sub"], risk_score=0.5)

    def validate(self, token: str) -> dict:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
