"""Continuous Face Zero Trust — Auth API Service."""
from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware.correlation import CorrelationMiddleware
from app.middleware.otel import OpenTelemetryMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routes import auth, enrollment, health, sessions
from app.routes import token as token_routes

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting auth-api", env=settings.ENVIRONMENT)
    yield
    logger.info("Shutting down auth-api")


app = FastAPI(
    title="Continuous Face Zero Trust — Auth API",
    description="Privacy-preserving continuous face-based zero-trust authentication",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CorrelationMiddleware)
app.add_middleware(OpenTelemetryMiddleware)

app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(enrollment.router, prefix="/api/v1/enrollment", tags=["enrollment"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(token_routes.router, prefix="/api/v1/tokens", tags=["tokens"])
