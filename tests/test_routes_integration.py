from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import router
from app.services.auth import AuthService
from app.services.load_balancer import LoadBalancer
from app.services.prefix_cache import PrefixCache
from app.services.proxy import ProxyService
from app.services.rate_limiter import RateLimiter
from app.services.router import RouterService
from app.services.scheduler import Scheduler


class FakeTransport:
    def __init__(self, name):
        self.name = name
        self.in_flight = 0
        self.last_latency = None
        self.is_open = False
        self.calls = 0

    async def post_json(self, endpoint, headers, body):
        self.calls += 1

        class R:
            status_code = 200
            headers = {"content-type": "application/json"}

            def json(inner_self):
                return {"backend": self.name, "model": body.get("model")}

        return R()


class FakePool:
    def __init__(self, names):
        self._transports = {name: FakeTransport(name) for name in names}

    def get(self, name):
        return self._transports[name]


def build_app(config, rate_capacity=1000):
    app = FastAPI()
    app.include_router(router)
    pool = FakePool([b.name for b in config.backends])
    app.state.auth_service = AuthService(config)
    app.state.router_service = RouterService(config)
    app.state.transport_pool = pool
    app.state.load_balancer = LoadBalancer(pool)
    app.state.prefix_cache = PrefixCache()
    app.state.rate_limiter = RateLimiter(
        capacity=rate_capacity, refill_rate=1000)
    app.state.scheduler = Scheduler(max_concurrent=10)
    app.state.proxy_service = ProxyService()
    return app, pool


def test_chat_completions_round_trip(base_config):
    app, pool = build_app(base_config)
    client = TestClient(app)
    response = client.post(
        "/v1/chat/completions", json={"messages": [{"role": "user", "content": "hi"}]})
    assert response.status_code == 200
    assert response.json()["model"] == "llama-fast"


def test_embeddings_routes_to_embeddings_backend(base_config):
    app, pool = build_app(base_config)
    client = TestClient(app)
    response = client.post("/v1/embeddings", json={"input": ["a"]})
    assert response.status_code == 200
    assert response.json()["backend"] == "embeddings"


def test_tools_route_to_qwen(base_config):
    app, pool = build_app(base_config)
    client = TestClient(app)
    response = client.post(
        "/v1/chat/completions", json={"messages": [{"role": "user", "content": "hi"}], "tools": [{"name": "x"}]}
    )
    assert response.status_code == 200
    assert response.json()["backend"] == "qwen-tools"


def test_rate_limit_returns_429(base_config):
    app, pool = build_app(base_config, rate_capacity=1)
    app.state.rate_limiter = RateLimiter(capacity=1, refill_rate=0.0)
    client = TestClient(app)
    first = client.post("/v1/chat/completions", json={"messages": []})
    second = client.post("/v1/chat/completions", json={"messages": []})
    assert first.status_code == 200
    assert second.status_code == 429


def test_invalid_json_returns_400(base_config):
    app, pool = build_app(base_config)
    client = TestClient(app)
    response = client.post(
        "/v1/chat/completions", content=b"not json", headers={"content-type": "application/json"}
    )
    assert response.status_code == 400


def test_backends_list_returns_health(base_config):
    app, pool = build_app(base_config)

    async def health_check_all():
        return [{"name": n, "healthy": True} for n in pool._transports]

    pool.health_check_all = health_check_all
    client = TestClient(app)
    response = client.get("/v1/backends")
    assert response.status_code == 200
    assert len(response.json()) == len(base_config.backends)


def test_prefix_cache_prefers_previously_used_backend(base_config):
    app, pool = build_app(base_config)
    client = TestClient(app)
    body = {"messages": [{"role": "user", "content": "same prefix"}]}
    first = client.post("/v1/chat/completions", json=body)
    used_first = first.json()["backend"]
    second = client.post("/v1/chat/completions", json=body)
    used_second = second.json()["backend"]
    assert used_first == used_second
