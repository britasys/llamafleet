from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx


class CircuitOpenError(Exception):
    """Raised when a backend's circuit breaker is open; call was short-circuited."""

    def __init__(self, backend_name: str):
        self.backend_name = backend_name
        super().__init__(f"Circuit open for backend '{backend_name}'")


class BackendTransport:
    def __init__(
        self,
        name: str,
        base_url: str,
        request_timeout: float,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ):
        self.name = name
        self.base_url = base_url.rstrip("/")

        # Bounded timeout for normal JSON calls; unbounded READ (but bounded
        # connect/write/pool) for streaming, since inference streams can
        # legitimately run for a long time.
        self._timeout = httpx.Timeout(
            connect=5.0, read=request_timeout, write=request_timeout, pool=5.0
        )
        self._stream_timeout = httpx.Timeout(
            connect=5.0, read=None, write=request_timeout, pool=5.0
        )

        limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        )
        self._client = httpx.AsyncClient(limits=limits)

        # --- circuit breaker state ---
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._consecutive_failures = 0
        self._opened_at: float | None = None

        # --- telemetry the scheduler / load balancer can read directly ---
        self.in_flight = 0
        self.last_latency: float | None = None

    # ---- circuit breaker ---------------------------------------------------

    @property
    def is_open(self) -> bool:
        if self._opened_at is None:
            return False
        if time.monotonic() - self._opened_at >= self._recovery_timeout:
            return False  # half-open: let a trial request through
        return True

    def _record_success(self) -> None:
        self._consecutive_failures = 0
        self._opened_at = None

    def _record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self._failure_threshold:
            self._opened_at = time.monotonic()

    # ---- requests -----------------------------------------------------------

    def _url(self, endpoint: str) -> str:
        return f"{self.base_url}{endpoint}"

    async def post_json(self, endpoint: str, headers: dict, body: dict) -> httpx.Response:
        if self.is_open:
            raise CircuitOpenError(self.name)
        self.in_flight += 1
        started = time.monotonic()
        try:
            response = await self._client.post(
                self._url(endpoint), headers=headers, json=body, timeout=self._timeout
            )
            self._record_success()
            return response
        except httpx.HTTPError:
            self._record_failure()
            raise
        finally:
            self.in_flight -= 1
            self.last_latency = time.monotonic() - started

    @asynccontextmanager
    async def post_stream(
        self, endpoint: str, headers: dict, body: dict
    ) -> AsyncIterator[httpx.Response]:
        """
        Yields an httpx.Response ready for .aiter_bytes(). Guarantees the
        underlying connection is released exactly once, whether the caller
        consumes the full stream, breaks early, or the stream errors out
        mid-flight — the original code leaked the client/response on any
        exception raised during iteration.
        """
        if self.is_open:
            raise CircuitOpenError(self.name)
        self.in_flight += 1
        started = time.monotonic()
        request = self._client.build_request(
            "POST", self._url(endpoint), headers=headers, json=body, timeout=self._stream_timeout
        )
        try:
            response = await self._client.send(request, stream=True)
            try:
                yield response
                self._record_success()
            except Exception:
                self._record_failure()
                raise
            finally:
                await response.aclose()
        except httpx.HTTPError:
            self._record_failure()
            raise
        finally:
            self.in_flight -= 1
            self.last_latency = time.monotonic() - started

    async def get(self, endpoint: str, timeout: float = 2.0) -> httpx.Response:
        return await self._client.get(self._url(endpoint), timeout=timeout)

    async def aclose(self) -> None:
        await self._client.aclose()
