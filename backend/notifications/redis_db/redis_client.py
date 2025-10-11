import redis.asyncio as redis
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

redis_client: redis.Redis | None = None

async def get_redis() -> redis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
        logger.info("Connected to Redis")
    return redis_client

async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")
        redis_client = None
