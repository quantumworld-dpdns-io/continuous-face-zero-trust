"""Authentication middleware."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

EXEMPT_PATHS = {"/health", "/ready", "/docs", "/openapi.json", "/api/v1/auth/login"}

from app.core.token_service import TokenService

ts = TokenService()


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = ts.validate(token)
                request.state.user = payload
            except Exception:
                pass

        return await call_next(request)
