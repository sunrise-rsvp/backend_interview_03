import json
import os
from typing import Optional, Any, Dict
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()


class RedisClient:
    """Async Redis client for caching operations"""
    
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._client: Optional[redis.Redis] = None
    
    async def get_client(self) -> redis.Redis:
        """Get or create Redis client connection"""
        if self._client is None:
            self._client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
        return self._client
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a value from Redis cache"""
        try:
            client = await self.get_client()
            value = await client.get(key)
            if value:
                return json.loads(value)
            return None
        except (redis.RedisError, json.JSONDecodeError) as e:
            print(f"Redis GET error for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: Dict[str, Any], 
        ttl: int = 3600
    ) -> bool:
        """Set a value in Redis cache with TTL"""
        try:
            client = await self.get_client()
            serialized_value = json.dumps(value, default=str)
            return await client.set(key, serialized_value, ex=ttl)
        except (redis.RedisError, json.JSONEncodeError) as e:
            print(f"Redis SET error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete a key from Redis cache"""
        try:
            client = await self.get_client()
            result = await client.delete(key)
            return result > 0
        except redis.RedisError as e:
            print(f"Redis DELETE error for key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern"""
        try:
            client = await self.get_client()
            keys = await client.keys(pattern)
            if keys:
                return await client.delete(*keys)
            return 0
        except redis.RedisError as e:
            print(f"Redis DELETE PATTERN error for pattern {pattern}: {e}")
            return 0
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis"""
        try:
            client = await self.get_client()
            return await client.exists(key) > 0
        except redis.RedisError as e:
            print(f"Redis EXISTS error for key {key}: {e}")
            return False
    
    async def ping(self) -> bool:
        """Check Redis connection health"""
        try:
            client = await self.get_client()
            result = await client.ping()
            return result is True
        except redis.RedisError as e:
            print(f"Redis PING error: {e}")
            return False
    
    async def close(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            self._client = None


# Global Redis client instance
redis_client = RedisClient()
