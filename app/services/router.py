from app.core.config import AppConfig, BackendConfig
from app.core.errors import backend_not_found
from app.services.proxy import ProxyService


class RouterService:
    def __init__(self, config: AppConfig, proxy_service: ProxyService):
        self.config = config
        self.proxy_service = proxy_service
        self.backends = {backend.name: backend for backend in config.backends}

    def get_backend(self, endpoint: str, body: dict) -> BackendConfig:
        model = body.get("model")
        requires_tools = bool(body.get("tools"))

        for rule in self.config.routing.rules:
            if rule.endpoint and rule.endpoint != endpoint:
                continue
            if rule.model and rule.model != model:
                continue
            if rule.requires_tools is not None and rule.requires_tools != requires_tools:
                continue
            return self._backend(rule.backend)

        return self._backend(self.config.routing.default_backend)

    async def list_backends(self) -> dict:
        return {
            "object": "list",
            "data": [
                {
                    "name": backend.name,
                    "model": backend.model,
                    "object": "backend",
                    "owned_by": "llama.cpp",
                    "healthy": (await self.proxy_service.health(backend))["healthy"],
                }
                for backend in sorted(self.config.backends, key=lambda item: item.priority)
            ],
        }

    def _backend(self, name: str) -> BackendConfig:
        backend = self.backends.get(name)
        if backend is None:
            raise backend_not_found(name)
        return backend
