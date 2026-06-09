"""Dependency injection container."""
from __future__ import annotations

import redis.asyncio as aioredis

from app.config import settings

_redis_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL, decode_responses=True, max_connections=20
        )
    return _redis_pool


async def get_face_ml_client():
    import httpx
    async with httpx.AsyncClient(base_url=settings.FACE_ML_URL, timeout=10.0) as client:
        yield client


async def get_zk_client():
    import httpx
    async with httpx.AsyncClient(base_url=settings.ZK_PROOFS_URL, timeout=10.0) as client:
        yield client


async def get_quantum_rng_client():
    import httpx
    async with httpx.AsyncClient(base_url=settings.QUANTUM_RNG_URL, timeout=10.0) as client:
        yield client


async def get_pqc_client():
    import httpx
    async with httpx.AsyncClient(base_url=settings.PQC_CRYPTO_URL, timeout=10.0) as client:
        yield client
