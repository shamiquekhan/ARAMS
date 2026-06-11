import json
from typing import Any, Dict, Optional
from app.core.config import settings


class ShortTermMemory:
    def __init__(self):
        self._client = None
        self.ttl = 7200

    @property
    def client(self):
        if self._client is None:
            try:
                import redis
                self._client = redis.Redis.from_url(settings.REDIS_URL)
            except Exception:
                self._client = None
        return self._client

    def save(self, session_id: str, key: str, value: Any):
        c = self.client
        if c is None:
            return
        try:
            c.hset(f"session:{session_id}", key, json.dumps(value))
            c.expire(f"session:{session_id}", self.ttl)
        except Exception:
            pass

    def get(self, session_id: str, key: str) -> Any:
        c = self.client
        if c is None:
            return None
        try:
            val = c.hget(f"session:{session_id}", key)
            return json.loads(val) if val else None
        except Exception:
            return None

    def get_all(self, session_id: str) -> Dict[str, Any]:
        c = self.client
        if c is None:
            return {}
        try:
            data = c.hgetall(f"session:{session_id}")
            return {k.decode(): json.loads(v) for k, v in data.items()}
        except Exception:
            return {}
