from app.services.rate_limiter import RateLimiter


def test_allows_up_to_capacity(monkeypatch):
    t = [0.0]
    monkeypatch.setattr("time.monotonic", lambda: t[0])
    limiter = RateLimiter(capacity=3, refill_rate=1.0)
    assert limiter.allow("k")
    assert limiter.allow("k")
    assert limiter.allow("k")
    assert not limiter.allow("k")


def test_refills_over_time(monkeypatch):
    t = [0.0]
    monkeypatch.setattr("time.monotonic", lambda: t[0])
    limiter = RateLimiter(capacity=1, refill_rate=1.0)
    assert limiter.allow("k")
    assert not limiter.allow("k")
    t[0] = 1.0
    assert limiter.allow("k")


def test_keys_are_independent(monkeypatch):
    t = [0.0]
    monkeypatch.setattr("time.monotonic", lambda: t[0])
    limiter = RateLimiter(capacity=1, refill_rate=1.0)
    assert limiter.allow("a")
    assert limiter.allow("b")
    assert not limiter.allow("a")


def test_retry_after_is_zero_when_allowed(monkeypatch):
    t = [0.0]
    monkeypatch.setattr("time.monotonic", lambda: t[0])
    limiter = RateLimiter(capacity=5, refill_rate=1.0)
    assert limiter.retry_after("k") == 0.0


def test_retry_after_positive_when_exhausted(monkeypatch):
    t = [0.0]
    monkeypatch.setattr("time.monotonic", lambda: t[0])
    limiter = RateLimiter(capacity=1, refill_rate=2.0)
    limiter.allow("k")
    assert limiter.retry_after("k") > 0


def test_retry_after_zero_refill_rate_does_not_crash(monkeypatch):
    t = [0.0]
    monkeypatch.setattr("time.monotonic", lambda: t[0])
    limiter = RateLimiter(capacity=1, refill_rate=0.0)
    limiter.allow("k")
    assert limiter.retry_after("k") == float("inf")
