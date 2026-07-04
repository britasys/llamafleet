from __future__ import annotations

from app.core.config import AppConfig
from app.services.backend_transport import BackendTransport


class TransportPool:
    def __init__(self, config: AppConfig):
        self._transports: dict[str, BackendTransport] = {
            backend.name: BackendTransport(
                name=backend.name,
                base_url=backend.url,
                request_timeout=config.server.request_timeout_seconds,
            )
            for backend in config.backends
        }

    def get(self, name: str) -> BackendTransport:
        try:
            return self._transports[name]
        except KeyError:
            raise LookupError(f"No transport configured for backend '{name}'")

    def all(self) -> dict[str, BackendTransport]:
        return self._transports

    async def health_check_all(self) -> list[dict]:
        results = []
        for transport in self._transports.values():
            try:
                response = await transport.get("/health")
                results.append(
                    {
                        "name": transport.name,
                        "status": response.status_code,
                        "healthy": response.is_success,
                        "in_flight": transport.in_flight,
                        "last_latency": transport.last_latency,
                        "circuit_open": transport.is_open,
                    }
                )
            except Exception:
                results.append(
                    {
                        "name": transport.name,
                        "status": None,
                        "healthy": False,
                        "in_flight": transport.in_flight,
                        "last_latency": transport.last_latency,
                        "circuit_open": transport.is_open,
                    }
                )
        return results

    async def aclose_all(self) -> None:
        for transport in self._transports.values():
            await transport.aclose()
