from redis.asyncio import Redis
import json
from config.settings import settings
from datetime import datetime, timezone

REDIS_URL = settings.REDIS_URL
redis = Redis.from_url(REDIS_URL, decode_responses=True)

async def store_verification_code(email: str, payload: dict, ttl_minutes: int = 15):
    key = f"verify:{email.lower().strip()}"
    data = {
        "code": str(payload.get("code")),
        "username": payload.get("username"),
        "password": payload.get("password"),
        "attempts": 3,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await redis.set(key, json.dumps(data), ex=ttl_minutes*60)
    return data["code"]

async def get_verification_data(email: str):
    key = f"verify:{email.lower().strip()}"
    data = await redis.get(key)
    if data:
        return json.loads(data)
    return None

async def decrement_attempts(email: str):
    data = await get_verification_data(email)
    if not data:
        return None
    data["attempts"] -= 1
    key = f"verify:{email.lower().strip()}"
    ttl = await redis.ttl(key)
    if ttl > 0:
        await redis.set(key, json.dumps(data), ex=ttl)
    else:
        await redis.set(key, json.dumps(data), ex=15*60)
    return data

async def delete_verification_code(email: str) -> bool:
    key = f"verify:{email.lower().strip()}"
    result = await redis.delete(key)
    return result > 0
