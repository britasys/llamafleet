from __future__ import annotations

from app.core.config import BackendConfig
from app.services.transport_pool import TransportPool


class NoHealthyBackendError(Exception):
    def __init__(self, model: str):
        self.model = model
        super().__init__(f"No healthy backend available for model '{model}'")


class LoadBalancer:
    def __init__(self, transport_pool: TransportPool):
        self._transport_pool = transport_pool

    def pick(self, candidates: list[BackendConfig], preferred_name: str | None = None) -> BackendConfig:
        if not candidates:
            raise NoHealthyBackendError("unknown")

        healthy = []
        for backend in candidates:
            transport = self._transport_pool.get(backend.name)
            if transport.is_open:
                continue
            score = float(transport.in_flight)
            if transport.last_latency:
                score += transport.last_latency
            if preferred_name and backend.name == preferred_name:
                score -= 1_000_000
            healthy.append((score, backend))

        if not healthy:
            raise NoHealthyBackendError(candidates[0].model)

        healthy.sort(key=lambda pair: pair[0])
        return healthy[0][1]
