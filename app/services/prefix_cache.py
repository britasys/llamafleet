from __future__ import annotations

import time


class PrefixCache:
    def __init__(self, max_entries: int = 10000, ttl_seconds: float = 600.0):
        self._ttl = ttl_seconds
        self._max_entries = max_entries
        self._entries: dict[str, tuple[str, float]] = {}

    @staticmethod
    def _key(prefix: str) -> str:
        return prefix[:256]

    def lookup(self, prefix: str) -> str | None:
        key = self._key(prefix)
        entry = self._entries.get(key)
        if entry is None:
            return None
        backend_name, expires_at = entry
        if time.monotonic() > expires_at:
            del self._entries[key]
            return None
        return backend_name

    def record(self, prefix: str, backend_name: str) -> None:
        if len(self._entries) >= self._max_entries:
            oldest_key = min(self._entries, key=lambda k: self._entries[k][1])
            del self._entries[oldest_key]
        key = self._key(prefix)
        self._entries[key] = (backend_name, time.monotonic() + self._ttl)


def extract_prefix(body: dict) -> str | None:
    messages = body.get("messages")
    if messages:
        content = messages[0].get("content")
        if isinstance(content, str):
            return content
        return None
    prompt = body.get("prompt")
    if isinstance(prompt, str):
        return prompt
    return None
