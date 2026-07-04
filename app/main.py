from fastapi import FastAPI
from fastapi.responses import Response

from app.api.openai import config, proxy_service, router as openai_router
from app.core.metrics import render_metrics

app = FastAPI(title=config.server.name)
app.include_router(openai_router)


@app.get("/health")
@app.get("/health/")
async def health():
    results = [await proxy_service.health(backend) for backend in config.backends]
    return {"status": "ok", "backends": results}


@app.get("/metrics")
@app.get("/metrics/")
async def metrics():
    return Response(render_metrics(), media_type="text/plain")
