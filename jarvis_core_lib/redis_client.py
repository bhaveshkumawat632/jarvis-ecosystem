import os
import redis.asyncio as redis

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_URL = f"redis://{REDIS_HOST}:6379/0"

def get_redis_client():
    return redis.from_url(REDIS_URL, decode_responses=True)
