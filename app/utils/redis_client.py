import redis.asyncio as redis
import json
from typing import Optional

# Redis 서버 URL 환경변수에 맞게 수정해주세요
redis_client = redis.from_url("redis://localhost", encoding="utf-8", decode_responses=True)

async def get_cached_weather(region_key: str) -> Optional[dict]:
    data = await redis_client.get(region_key)
    if data:
        return json.loads(data)
    return None

async def set_cached_weather(region_key: str, weather_data: dict, expire_seconds: int = 3600):
    await redis_client.set(region_key, json.dumps(weather_data), ex=expire_seconds)
