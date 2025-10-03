import json
from redis.asyncio import Redis
from config.settings import settings
from datetime import datetime, timezone
from .redis_store import get_verification_data

redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)

async def store_forgot_password_code(email: str, code: str, ttl_minutes: int = 15):
    key = f"verify:{email.lower().strip()}"
    data = {
        "code": str(code),
        "verified": False,
        "attempts": 3,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await redis.set(key, json.dumps(data), ex=ttl_minutes*60)
    return data


async def mark_forgot_password_verified(email: str):
    data = await get_verification_data(email)
    if not data:
        return None
    data["verified"] = True
    key = f"verify:{email.lower().strip()}"
    ttl = await redis.ttl(key)
    if ttl > 0:
        await redis.set(key, json.dumps(data), ex=ttl)
    else:
        await redis.set(key, json.dumps(data), ex=15*60)
    return data

