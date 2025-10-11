from fastapi import APIRouter
from services.utils import get_event_from_redis

router = APIRouter()
@router.get("/get_redis_info")
async def get_info_from_redis(key: str):
    result = await get_event_from_redis(key)
    return result