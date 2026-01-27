"""Redis client configuration."""

from typing import Optional

import redis.asyncio as redis
from redis.asyncio import Redis

from src.core.config import settings

_redis_client: Optional[Redis] = None


async def get_redis() -> Redis:
    """Get Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


class CacheService:
    """Cache service using Redis."""

    def __init__(self, client: Redis):
        self.client = client
        self.default_ttl = 300  # 5 minutes

    async def get(self, key: str) -> Optional[str]:
        """Get cached value."""
        return await self.client.get(key)

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """Set cached value with TTL."""
        await self.client.set(key, value, ex=ttl or self.default_ttl)

    async def delete(self, key: str) -> None:
        """Delete cached key."""
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return await self.client.exists(key) > 0

    async def increment(self, key: str, ttl: Optional[int] = None) -> int:
        """Increment counter, optionally with TTL."""
        value = await self.client.incr(key)
        if ttl and value == 1:
            await self.client.expire(key, ttl)
        return value
