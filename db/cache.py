"""
Redis caching utility.
"""
import os
import json
import logging
from redis import asyncio as aioredis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

# Note: Redis integration into API routes is deferred to Phase 4.
# These utilities will be used then for caching screener results and ticker data.

async def get_cache(key: str):
    """
    Retrieve value from Redis cache.
    """
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        logger.error(f"Redis get error for {key}: {e}")
    return None

async def set_cache(key: str, value: dict, ttl: int = 300):
    """
    Store value in Redis cache with a TTL (default 5 minutes).
    """
    try:
        await redis_client.set(key, json.dumps(value), ex=ttl)
    except Exception as e:
        logger.error(f"Redis set error for {key}: {e}")
