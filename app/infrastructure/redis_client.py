import os
from upstash_redis import Redis
from typing import Optional

class RedisClient:
    def __init__(self):
        url = os.environ.get("UPSTASH_REDIS_REST_URL")
        token = os.environ.get("UPSTASH_REDIS_REST_TOKEN")
        self.redis = None
        if url and token:
            self.redis = Redis(url=url, token=token)

    def get_client(self) -> Optional[Redis]:
        return self.redis

redis_service = RedisClient()
