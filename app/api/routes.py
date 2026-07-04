from fastapi import APIRouter, Request

from app.core.errors import invalid_request, too_many_requests, scheduler_saturated
from app.services.prefix_cache import extract_prefix
from app.services.scheduler import Priority, SchedulerTimeoutError

router = APIRouter()


async def handle(request: Request, endpoint: str):
    state = request.app.state
    state.auth_service.verify(request)

    key = request.headers.get("authorization") or (request.client.host if request.client else "anonymous")
    if not state.rate_limiter.allow(key):
        raise too_many_requests(state.rate_limiter.retry_after(key))

    try:
        body = await request.json()
    except ValueError:
        raise invalid_request("Request body must be valid JSON")

    candidates = state.router_service.get_backends(endpoint, body)
    prefix = extract_prefix(body)
    hint = state.prefix_cache.lookup(prefix) if prefix else None
    backend = state.load_balancer.pick(candidates, hint)
    if prefix:
        state.prefix_cache.record(prefix, backend.name)

    transport = state.transport_pool.get(backend.name)

    try:
        async with state.scheduler.slot(Priority.NORMAL):
            return await state.proxy_service.forward(request, transport, backend, endpoint, body)
    except SchedulerTimeoutError:
        raise scheduler_saturated()


@router.get("/v1/backends")
async def backends(request: Request):
    request.app.state.auth_service.verify(request)
    return await request.app.state.transport_pool.health_check_all()


@router.post("/v1/chat/completions")
async def chat_completions(request: Request):
    return await handle(request, "/v1/chat/completions")


@router.post("/v1/completions")
async def completions(request: Request):
    return await handle(request, "/v1/completions")


@router.post("/v1/embeddings")
async def embeddings(request: Request):
    return await handle(request, "/v1/embeddings")


@router.post("/v1/responses")
async def responses(request: Request):
    return await handle(request, "/v1/responses")


@router.post("/v1/rerank")
async def rerank(request: Request):
    return await handle(request, "/v1/rerank")