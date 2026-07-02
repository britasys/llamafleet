from time import perf_counter

import httpx
from fastapi import Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from app.core.config import BackendConfig
from app.core.errors import backend_unavailable
from app.core.metrics import LATENCY, REQUESTS


class ProxyService:
    def __init__(self, timeout: float):
        self.timeout = timeout

    async def forward(self, request: Request, backend: BackendConfig, endpoint: str, body: dict) -> Response:
        started = perf_counter()
        url = f"{backend.url.rstrip('/')}{endpoint}"
        headers = self._headers(request)
        body = dict(body)
        body["model"] = backend.model
        stream = bool(body.get("stream"))

        try:
            if stream:
                response = await self._stream(url, headers, body)
            else:
                response = await self._json(url, headers, body)
            REQUESTS.labels(endpoint=endpoint, backend=backend.name, status=str(response.status_code)).inc()
            return response
        except httpx.HTTPError:
            REQUESTS.labels(endpoint=endpoint, backend=backend.name, status="502").inc()
            raise backend_unavailable(backend.name)
        finally:
            LATENCY.labels(endpoint=endpoint, backend=backend.name).observe(perf_counter() - started)

    async def health(self, backend: BackendConfig) -> dict:
        url = f"{backend.url.rstrip()}/health"
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(url)
            return {"name": backend.name, "status": response.status_code, "healthy": response.is_success}
        except httpx.HTTPError:
            return {"name": backend.name, "status": None, "healthy": False}

    async def _json(self, url: str, headers: dict, body: dict) -> JSONResponse:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=body)
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return JSONResponse(status_code=response.status_code, content=response.json())
        return JSONResponse(status_code=response.status_code, content={"detail": response.text})

    async def _stream(self, url: str, headers: dict, body: dict) -> StreamingResponse:
        client = httpx.AsyncClient(timeout=None)
        request = client.build_request("POST", url, headers=headers, json=body)
        response = await client.send(request, stream=True)

        async def iterator():
            async for chunk in response.aiter_bytes():
                yield chunk
            await response.aclose()
            await client.aclose()

        return StreamingResponse(
            iterator(),
            status_code=response.status_code,
            media_type=response.headers.get("content-type", "text/event-stream"),
        )

    def _headers(self, request: Request) -> dict:
        excluded = {"host", "content-length"}
        return {key: value for key, value in request.headers.items() if key.lower() not in excluded}
