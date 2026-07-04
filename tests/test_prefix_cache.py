from app.services.prefix_cache import PrefixCache, extract_prefix


def test_extract_prefix_from_messages():
    assert extract_prefix(
        {"messages": [{"role": "user", "content": "hi"}]}) == "hi"


def test_extract_prefix_from_prompt():
    assert extract_prefix({"prompt": "hello"}) == "hello"


def test_extract_prefix_none_when_missing():
    assert extract_prefix({}) is None


def test_extract_prefix_none_for_non_string_content():
    assert extract_prefix(
        {"messages": [{"role": "user", "content": [1, 2]}]}) is None


def test_lookup_miss_returns_none():
    cache = PrefixCache()
    assert cache.lookup("nope") is None


def test_record_then_lookup(monkeypatch):
    t = [0.0]
    monkeypatch.setattr("time.monotonic", lambda: t[0])
    cache = PrefixCache(ttl_seconds=10)
    cache.record("hello", "backend-a")
    assert cache.lookup("hello") == "backend-a"


def test_entry_expires(monkeypatch):
    t = [0.0]
    monkeypatch.setattr("time.monotonic", lambda: t[0])
    cache = PrefixCache(ttl_seconds=5)
    cache.record("hello", "backend-a")
    t[0] = 6.0
    assert cache.lookup("hello") is None


def test_eviction_when_full(monkeypatch):
    t = [0.0]
    monkeypatch.setattr("time.monotonic", lambda: t[0])
    cache = PrefixCache(max_entries=2, ttl_seconds=100)
    cache.record("a", "backend-a")
    t[0] = 1.0
    cache.record("b", "backend-b")
    t[0] = 2.0
    cache.record("c", "backend-c")
    assert len(cache._entries) == 2
    assert cache.lookup("c") == "backend-c"
