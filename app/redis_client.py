import os
import redis
from dotenv import load_dotenv
import json

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Redis 연결 객체
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True  # 문자열 자동 디코딩
)

# 유틸 함수
def set_cache(key: str, value, ttl: int = 3600):
    """Redis에 값 저장 (ttl: 초)"""
    redis_client.set(key, json.dumps(value), ex=ttl)

def get_cache(key: str):
    """Redis에서 값 가져오기"""
    value = redis_client.get(key)
    if value:
        return json.loads(value)
    return None

def delete_cache(key: str):
    """Redis에서 키 삭제"""
    redis_client.delete(key)
