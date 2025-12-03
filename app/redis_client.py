import aioredis
import json
from dotenv import load_dotenv
import os

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

redis = aioredis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}", db=REDIS_DB)

async def set_cached_weather(key: str, value, expire_seconds: int = 3600):
    await redis.set(key, json.dumps(value), ex=expire_seconds)

async def get_cached_weather(key: str):
    data = await redis.get(key)
    if data:
        return json.loads(data)
    return None

async def delete_cached_weather(key: str):
    await redis.delete(key)
