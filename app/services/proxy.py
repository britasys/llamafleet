from __future__ import annotations

from time import perf_counter

import httpx
from fastapi import Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from app.core.config import BackendConfig
from app.core.errors import backend_overloaded, backend_unavailable
from app.core.metrics import LATENCY, REQUESTS
from app.services.backend_transport import BackendTransport, CircuitOpenError
from app.services.request_transformer import transform_body

# Never forward the caller's own credentials to a backend — a backend should
# only ever see the credential *we* configured for it (if any), not whatever
# token the client authenticated to the gateway with.
EXCLUDED_HEADERS = {"host", "content-length", "authorization"}


def _forward_headers(request: Request, backend: BackendConfig) -> dict:
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in EXCLUDED_HEADERS
    }
    api_key = getattr(backend, "api_key", None)
    if api_key:
        headers["authorization"] = f"Bearer {api_key}"
    return headers


class ProxyService:
    """Stateless — transports own all per-backend state (pooling, circuit breaker)."""

    async def forward(
        self,
        request: Request,
        transport: BackendTransport,
        backend: BackendConfig,
        endpoint: str,
        body: dict,
    ) -> Response:
        started = perf_counter()
        headers = _forward_headers(request, backend)
        body = transform_body(endpoint, body, backend)
        stream = bool(body.get("stream"))

        try:
            if stream:
                response = await self._stream(transport, endpoint, headers, body)
            else:
                response = await self._json(transport, endpoint, headers, body)
            REQUESTS.labels(
                endpoint=endpoint, backend=backend.name, status=str(response.status_code)
            ).inc()
            return response
        except CircuitOpenError:
            REQUESTS.labels(endpoint=endpoint, backend=backend.name, status="503").inc()
            raise backend_overloaded(backend.name)
        except httpx.HTTPError:
            REQUESTS.labels(endpoint=endpoint, backend=backend.name, status="502").inc()
            raise backend_unavailable(backend.name)
        finally:
            LATENCY.labels(endpoint=endpoint, backend=backend.name).observe(
                perf_counter() - started
            )

    async def _json(
        self, transport: BackendTransport, endpoint: str, headers: dict, body: dict
    ) -> JSONResponse:
        response = await transport.post_json(endpoint, headers, body)
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return JSONResponse(status_code=response.status_code, content=response.json())
        return JSONResponse(status_code=response.status_code, content={"detail": response.text})

    async def _stream(
        self, transport: BackendTransport, endpoint: str, headers: dict, body: dict
    ) -> StreamingResponse:
        # We need status_code/media_type before we can construct the
        # StreamingResponse, but the context manager that guarantees cleanup
        # is scoped with `async with`. So we enter it manually here and
        # close it from inside the generator below — this is the one place
        # that trade-off is made, and it's contained to this single method.
        ctx = transport.post_stream(endpoint, headers, body)
        response = await ctx.__aenter__()
        status_code = response.status_code
        media_type = response.headers.get("content-type", "text/event-stream")

        async def iterator():
            try:
                async for chunk in response.aiter_bytes():
                    yield chunk
            finally:
                await ctx.__aexit__(None, None, None)

        return StreamingResponse(iterator(), status_code=status_code, media_type=media_type)