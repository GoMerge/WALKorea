import redis.asyncio as redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

# 배포환경 자동 감지
IS_DOCKER = os.getenv("IS_DOCKER", "false").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "redis" if IS_DOCKER else "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

redis_client = redis.from_url(
    f"redis://{REDIS_HOST}:{REDIS_PORT}",
    db=REDIS_DB,
    encoding="utf-8",
    decode_responses=True,
)

async def set_cached(key: str, value, expire_seconds: int = 3600):
    await redis_client.set(key, json.dumps(value), ex=expire_seconds)

async def get_cached(key: str):
    data = await redis_client.get(key)
    if data:
        return json.loads(data)
    return None

async def delete_cached(key: str):
