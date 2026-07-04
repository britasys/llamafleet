from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class TokenBucket:
    capacity: float
    refill_rate: float
    tokens: float
    updated_at: float


class RateLimiter:
    def __init__(self, capacity: float = 60.0, refill_rate: float = 1.0):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self._buckets: dict[str, TokenBucket] = {}

    def _bucket(self, key: str) -> TokenBucket:
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = TokenBucket(
                self.capacity, self.refill_rate, self.capacity, time.monotonic())
            self._buckets[key] = bucket
        return bucket

    def _refill(self, bucket: TokenBucket) -> None:
        now = time.monotonic()
        elapsed = now - bucket.updated_at
        bucket.tokens = min(bucket.capacity, bucket.tokens +
                            elapsed * bucket.refill_rate)
        bucket.updated_at = now

    def allow(self, key: str, cost: float = 1.0) -> bool:
        bucket = self._bucket(key)
        self._refill(bucket)
        if bucket.tokens >= cost:
            bucket.tokens -= cost
            return True
        return False

    def retry_after(self, key: str, cost: float = 1.0) -> float:
        bucket = self._bucket(key)
        self._refill(bucket)
        deficit = cost - bucket.tokens
        return max(0.0, deficit / bucket.refill_rate)
