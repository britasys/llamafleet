from contextlib import asynccontextmanager

import httpx
import pytest
from fastapi import Request
from fastapi.responses import StreamingResponse

from app.services.backend_transport import CircuitOpenError
from app.services.proxy import ProxyService


def make_request(headers=None):
    headers = headers or {}
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/v1/chat/completions",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        "query_string": b"",
        "client": ("127.0.0.1", 1234),
    }
    return Request(scope)


class FakeResponse:
    def __init__(self, status_code=200, json_body=None, headers=None):
        self.status_code = status_code
        self._json = json_body or {}
        self.headers = headers or {"content-type": "application/json"}
        self.text = str(json_body)

    def json(self):
        return self._json


class FakeTransport:
    def __init__(self, json_response=None, raises=None, stream_chunks=None):
        self._json_response = json_response
        self._raises = raises
        self._stream_chunks = stream_chunks or []
        self.calls = []

    async def post_json(self, endpoint, headers, body):
        self.calls.append((endpoint, headers, body))
        if self._raises:
            raise self._raises
        return self._json_response

    @asynccontextmanager
    async def post_stream(self, endpoint, headers, body):
        self.calls.append((endpoint, headers, body))
        if self._raises:
            raise self._raises

        class R:
            status_code = 200
            headers = {"content-type": "text/event-stream"}

            async def aiter_bytes(inner_self):
                for chunk in self._stream_chunks:
                    yield chunk

        yield R()


class FakeBackend:
    name = "b1"
    model = "m1"
    prompt = None
    api_key = None


async def test_json_forward_returns_wrapped_response():
    transport = FakeTransport(json_response=FakeResponse(200, {"ok": True}))
    proxy = ProxyService()
    request = make_request()
    response = await proxy.forward(request, transport, FakeBackend(), "/v1/chat/completions", {"messages": []})
    assert response.status_code == 200
    assert transport.calls[0][2]["model"] == "m1"


async def test_authorization_header_stripped_from_forwarded_headers():
    transport = FakeTransport(json_response=FakeResponse(200, {"ok": True}))
    proxy = ProxyService()
    request = make_request(
        {"authorization": "Bearer secret", "x-custom": "keep-me"})
    await proxy.forward(request, transport, FakeBackend(), "/v1/chat/completions", {"messages": []})
    forwarded_headers = transport.calls[0][1]
    assert "authorization" not in forwarded_headers
    assert forwarded_headers.get("x-custom") == "keep-me"


async def test_http_error_raises_502():
    transport = FakeTransport(raises=httpx.ConnectError("down"))
    proxy = ProxyService()
    request = make_request()
    with pytest.raises(Exception) as exc_info:
        await proxy.forward(request, transport, FakeBackend(), "/v1/chat/completions", {"messages": []})
    assert getattr(exc_info.value, "status_code", None) == 502


async def test_circuit_open_raises_503():
    transport = FakeTransport(raises=CircuitOpenError("b1"))
    proxy = ProxyService()
    request = make_request()
    with pytest.raises(Exception) as exc_info:
        await proxy.forward(request, transport, FakeBackend(), "/v1/chat/completions", {"messages": []})
    assert getattr(exc_info.value, "status_code", None) == 503


async def test_stream_forward_returns_streaming_response():
    transport = FakeTransport(stream_chunks=[b"a", b"b", b"c"])
    proxy = ProxyService()
    request = make_request()
    response = await proxy.forward(
        request, transport, FakeBackend(
        ), "/v1/chat/completions", {"messages": [], "stream": True}
    )
    assert isinstance(response, StreamingResponse)
    collected = b""
    async for chunk in response.body_iterator:
        collected += chunk if isinstance(chunk, bytes) else chunk.encode()
    assert collected == b"abc"
