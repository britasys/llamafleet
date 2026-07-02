from fastapi import APIRouter, Request

from app.core.config import get_config
from app.services.auth import AuthService
from app.services.proxy import ProxyService
from app.services.router import RouterService

router = APIRouter()
config = get_config()
auth_service = AuthService(config)
router_service = RouterService(config)
proxy_service = ProxyService(config.server.request_timeout_seconds)


async def handle(request: Request, endpoint: str):
    auth_service.verify(request)
    body = await request.json()
    backend = router_service.get_backend(endpoint, body)
    return await proxy_service.forward(request, backend, endpoint, body)


@router.get("/v1/models")
async def models(request: Request):
    auth_service.verify(request)
    return router_service.list_models()


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
