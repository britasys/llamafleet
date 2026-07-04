import httpx
import pytest

from app.services.backend_transport import BackendTransport, CircuitOpenError


def mount(transport, handler):
    transport._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler))


async def test_post_json_success():
    def handler(request):
        return httpx.Response(200, json={"ok": True})

    t = BackendTransport("b", "http://x", request_timeout=5)
    mount(t, handler)
    response = await t.post_json("/v1/completions", {}, {"a": 1})
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert t.in_flight == 0
    assert t.last_latency is not None


async def test_post_json_failure_trips_circuit():
    def handler(request):
        raise httpx.ConnectError("boom", request=request)

    t = BackendTransport(
        "b", "http://x", request_timeout=5, failure_threshold=2)
    mount(t, handler)
    for _ in range(2):
        with pytest.raises(httpx.HTTPError):
            await t.post_json("/v1/completions", {}, {})
    assert t.is_open
    with pytest.raises(CircuitOpenError):
        await t.post_json("/v1/completions", {}, {})


async def test_circuit_recovers_after_timeout(monkeypatch):
    def handler(request):
        raise httpx.ConnectError("boom", request=request)

    t = BackendTransport("b", "http://x", request_timeout=5,
                         failure_threshold=1, recovery_timeout=0.05)
    mount(t, handler)
    with pytest.raises(httpx.HTTPError):
        await t.post_json("/v1/completions", {}, {})
    assert t.is_open

    def ok_handler(request):
        return httpx.Response(200, json={"ok": True})

    import asyncio

    await asyncio.sleep(0.1)
    assert not t.is_open
    mount(t, ok_handler)
    response = await t.post_json("/v1/completions", {}, {})
    assert response.status_code == 200


async def test_post_stream_yields_chunks():
    def handler(request):
        return httpx.Response(200, content=b"abcdef", headers={"content-type": "text/event-stream"})

    t = BackendTransport("b", "http://x", request_timeout=5)
    mount(t, handler)
    chunks = b""
    async with t.post_stream("/v1/chat/completions", {}, {}) as response:
        async for chunk in response.aiter_bytes():
            chunks += chunk
    assert chunks == b"abcdef"
    assert t.in_flight == 0


async def test_post_stream_failure_releases_in_flight():
    def handler(request):
        raise httpx.ConnectError("boom", request=request)

    t = BackendTransport("b", "http://x", request_timeout=5)
    mount(t, handler)
    with pytest.raises(httpx.HTTPError):
        async with t.post_stream("/v1/chat/completions", {}, {}) as response:
            async for _ in response.aiter_bytes():
                pass
    assert t.in_flight == 0
