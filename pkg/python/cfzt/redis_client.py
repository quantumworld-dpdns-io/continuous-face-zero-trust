"""Redis client wrapper with connection pooling."""
from __future__ import annotations

import redis.asyncio as aioredis
from redis.asyncio import ConnectionPool, Redis


class RedisClient:
    def __init__(self, url: str = "redis://localhost:6379", max_connections: int = 20):
        self.pool = ConnectionPool.from_url(url, max_connections=max_connections, decode_responses=True)

    def client(self) -> Redis:
        return Redis(connection_pool=self.pool)

    async def close(self):
        await self.pool.disconnect()

    async def health_check(self) -> bool:
        try:
            async with self.client() as conn:
                return await conn.ping()
        except Exception:
            return False
