"""
Redis Connection Manager

Provides a singleton Redis connection for caching, rate limiting,
and pub/sub operations.
"""
from typing import Optional

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from app.core.config import get_settings

settings = get_settings()

# Global connection pool
_pool: Optional[ConnectionPool] = None


def get_redis_pool() -> ConnectionPool:
    """
    Get or create Redis connection pool.

    Returns:
        ConnectionPool: Redis connection pool

    Raises:
        ValueError: If redis_url is not configured
    """
    global _pool
    if _pool is None:
        _pool = ConnectionPool.from_url(
            settings.redis_url,
            decode_responses=settings.redis_decode_responses,
        )
    return _pool


async def get_redis() -> redis.Redis:
    """
    Get Redis client instance.

    This is a dependency function that can be used with FastAPI.

    Yields:
        redis.Redis: Redis client

    Example:
        @app.get("/cache")
        async def get_cache(r: redis.Redis = Depends(get_redis)):
            value = await r.get("key")
            return {"value": value}
    """
    pool = get_redis_pool()
    async with redis.Redis(connection_pool=pool) as client:
        yield client


async def close_redis() -> None:
    """Close Redis connection pool."""
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


class RedisManager:
    """
    High-level Redis manager for common operations.

    Provides methods for caching, rate limiting, and pub/sub.
    """

    def __init__(self, client: redis.Redis):
        """
        Initialize Redis manager.

        Args:
            client: Redis client instance
        """
        self.client = client

    async def get(self, key: str) -> Optional[str]:
        """
        Get value from Redis.

        Args:
            key: Redis key

        Returns:
            Value if exists, None otherwise
        """
        return await self.client.get(key)

    async def set(
        self,
        key: str,
        value: str,
        expire: Optional[int] = None,
    ) -> bool:
        """
        Set value in Redis.

        Args:
            key: Redis key
            value: Value to set
            expire: Expiration time in seconds (optional)

        Returns:
            True if successful
        """
        return await self.client.set(key, value, ex=expire)

    async def delete(self, *keys: str) -> int:
        """
        Delete keys from Redis.

        Args:
            *keys: Keys to delete

        Returns:
            Number of keys deleted
        """
        return await self.client.delete(*keys)

    async def exists(self, *keys: str) -> int:
        """
        Check if keys exist.

        Args:
            *keys: Keys to check

        Returns:
            Number of existing keys
        """
        return await self.client.exists(*keys)

    async def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration time for a key.

        Args:
            key: Redis key
            seconds: Expiration time in seconds

        Returns:
            True if successful
        """
        return await self.client.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        """
        Get time to live for a key.

        Args:
            key: Redis key

        Returns:
            TTL in seconds, -1 if no expiration, -2 if key doesn't exist
        """
        return await self.client.ttl(key)

    async def incr(self, key: str, amount: int = 1) -> int:
        """
        Increment value.

        Args:
            key: Redis key
            amount: Amount to increment by

        Returns:
            New value
        """
        return await self.client.incr(key, amount)

    async def incr_with_expiry(
        self,
        key: str,
        amount: int = 1,
        expire: int = 60,
    ) -> int:
        """
        Increment value and set expiration if key doesn't exist.

        Useful for rate limiting.

        Args:
            key: Redis key
            amount: Amount to increment by
            expire: Expiration time in seconds

        Returns:
            New value
        """
        value = await self.client.incr(key, amount)
        if value == amount:
            await self.client.expire(key, expire)
        return value

    async def json_get(self, key: str) -> Optional[dict]:
        """
        Get JSON value from Redis.

        Args:
            key: Redis key

        Returns:
            Dict if exists, None otherwise
        """
        import json

        value = await self.client.get(key)
        if value:
            return json.loads(value)
        return None

    async def json_set(
        self,
        key: str,
        value: dict,
        expire: Optional[int] = None,
    ) -> bool:
        """
        Set JSON value in Redis.

        Args:
            key: Redis key
            value: Dict value to set
            expire: Expiration time in seconds (optional)

        Returns:
            True if successful
        """
        import json

        json_value = json.dumps(value)
        return await self.client.set(key, json_value, ex=expire)

    async def publish(self, channel: str, message: str) -> int:
        """
        Publish message to Redis channel.

        Args:
            channel: Channel name
            message: Message to publish

        Returns:
            Number of subscribers
        """
        return await self.client.publish(channel, message)

    async def subscribe(self, *channels: str) -> redis.client.PubSub:
        """
        Subscribe to Redis channels.

        Args:
            *channels: Channels to subscribe to

        Returns:
            PubSub instance
        """
        pubsub = self.client.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub
