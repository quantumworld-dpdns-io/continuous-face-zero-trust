"""JWT/PASETO token utilities."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError, ExpiredSignatureError

from cfzt.errors import UnauthenticatedError


class TokenManager:
    def __init__(self, secret: str, algorithm: str = "HS256", access_ttl_minutes: int = 15, refresh_ttl_days: int = 7):
        self.secret = secret
        self.algorithm = algorithm
        self.access_ttl = access_ttl_minutes
        self.refresh_ttl = refresh_ttl_days

    def create_access_token(self, subject: str, session_id: str | None = None, claims: dict | None = None) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": subject,
            "sid": session_id or str(uuid.uuid4()),
            "iat": now,
            "exp": now + timedelta(minutes=self.access_ttl),
            "type": "access",
        }
        if claims:
            payload.update(claims)
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def create_refresh_token(self, subject: str, session_id: str | None = None) -> str:
        now = datetime.now(timezone.utc)
        return jwt.encode(
            {"sub": subject, "sid": session_id or str(uuid.uuid4()), "iat": now, "exp": now + timedelta(days=self.refresh_ttl), "type": "refresh"},
            self.secret,
            algorithm=self.algorithm,
        )

    def create_token_pair(self, subject: str, claims: dict | None = None) -> dict:
        now = datetime.now(timezone.utc)
        session_id = str(uuid.uuid4())
        return {
            "access_token": self.create_access_token(subject, session_id, claims),
            "refresh_token": self.create_refresh_token(subject, session_id),
            "session_id": session_id,
            "expires_at": (now + timedelta(minutes=self.access_ttl)).isoformat(),
            "token_type": "Bearer",
        }

    def decode(self, token: str) -> dict:
        try:
            return jwt.decode(token, self.secret, algorithms=[self.algorithm])
        except ExpiredSignatureError:
            raise UnauthenticatedError("Token has expired")
        except JWTError:
            raise UnauthenticatedError("Invalid token")

    def is_refresh_token(self, token: str) -> bool:
        payload = self.decode(token)
        return payload.get("type") == "refresh"

    def get_subject(self, token: str) -> str:
        payload = self.decode(token)
        return payload.get("sub", "")
