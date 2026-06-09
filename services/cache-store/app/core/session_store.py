"""Session store using Redis hashes."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import redis.asyncio as aioredis


class SessionStore:
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.prefix = "session"
        self.ttl = 900

    async def create(self, session_id: str, data: dict) -> None:
        key = f"{self.prefix}:{session_id}"
        data["created_at"] = datetime.now(timezone.utc).isoformat()
        data["last_active"] = data["created_at"]
        await self.redis.hset(key, mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in data.items()})
        await self.redis.expire(key, self.ttl)
        await self.redis.sadd("active_sessions", session_id)

    async def get(self, session_id: str) -> dict | None:
        key = f"{self.prefix}:{session_id}"
        data = await self.redis.hgetall(key)
        if not data:
            return None
        await self.redis.expire(key, self.ttl)
        return data

    async def update(self, session_id: str, data: dict) -> None:
        key = f"{self.prefix}:{session_id}"
        data["last_active"] = datetime.now(timezone.utc).isoformat()
        await self.redis.hset(key, mapping={k: str(v) for k, v in data.items()})
        await self.redis.expire(key, self.ttl)

    async def delete(self, session_id: str) -> None:
        key = f"{self.prefix}:{session_id}"
        await self.redis.delete(key)
        await self.redis.srem("active_sessions", session_id)
