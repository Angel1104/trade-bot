from __future__ import annotations

import hashlib
import threading
import time
from typing import Optional

from cachetools import TTLCache

from .models import WebhookPayload


class IdempotencyStore:
    def __init__(self, ttl_seconds: int = 60, maxsize: int = 512):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl_seconds)
        self._lock = threading.Lock()

    def is_duplicate(self, key: str) -> bool:
        with self._lock:
            if key in self.cache:
                return True
            self.cache[key] = True
            return False


def build_idempotency_key(payload: WebhookPayload) -> str:
    if payload.event_id:
        return payload.event_id
    timestamp_ms = payload.ts or int(time.time() * 1000)
    bucket = int(timestamp_ms // 5000)  # 5s buckets to smooth out jitter
    raw = f"{payload.symbol}:{payload.action}:{payload.qty}:{bucket}:{payload.strategy or ''}"
    return hashlib.sha256(raw.encode()).hexdigest()
