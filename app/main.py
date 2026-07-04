from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_config
from app.services.auth import AuthService
from app.services.load_balancer import LoadBalancer
from app.services.prefix_cache import PrefixCache
from app.services.proxy import ProxyService
from app.services.rate_limiter import RateLimiter
from app.services.router import RouterService
from app.services.scheduler import Scheduler
from app.services.transport_pool import TransportPool


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = get_config()
    transport_pool = TransportPool(config)
    
    app.state.config = config
    app.state.auth_service = AuthService(config)
    app.state.transport_pool = transport_pool
    app.state.proxy_service = ProxyService()
    app.state.router_service = RouterService(config)
    app.state.load_balancer = LoadBalancer(transport_pool)
    app.state.prefix_cache = PrefixCache()
    app.state.rate_limiter = RateLimiter(
        capacity=config.server.rate_limit_capacity,
        refill_rate=config.server.rate_limit_refill_per_second,
    )
    app.state.scheduler = Scheduler(
        max_concurrent=config.server.max_concurrent_requests,
        max_queue=config.server.max_queue_size,
        queue_timeout=config.server.queue_timeout_seconds,
    )

    yield

    await transport_pool.aclose_all()


def create_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(router)
    return app


app = create_app()