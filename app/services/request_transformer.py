from __future__ import annotations

from typing import Callable

from app.core.config import BackendConfig

Transformer = Callable[[dict, BackendConfig], dict]


def _chat_completions(body: dict, backend: BackendConfig) -> dict:
    body = dict(body)
    body["model"] = backend.model
    if backend.prompt:
        messages = list(body.get("messages") or [])
        if not messages or messages[0].get("role") != "system":
            messages.insert(0, {"role": "system", "content": backend.prompt})
        body["messages"] = messages
    return body


def _completions(body: dict, backend: BackendConfig) -> dict:
    body = dict(body)
    body["model"] = backend.model
    if backend.prompt and "prompt" in body:
        body["prompt"] = f"{backend.prompt}\n\n{body['prompt']}"
    return body


def _passthrough_with_model(body: dict, backend: BackendConfig) -> dict:
    # embeddings, rerank: retarget the model, no prompt injection
    body = dict(body)
    body["model"] = backend.model
    return body


_TRANSFORMERS: dict[str, Transformer] = {
    "/v1/chat/completions": _chat_completions,
    "/v1/completions": _completions,
    "/v1/embeddings": _passthrough_with_model,
    "/v1/rerank": _passthrough_with_model,
    "/v1/responses": _chat_completions,
}


def transform_body(endpoint: str, body: dict, backend: BackendConfig) -> dict:
    transformer = _TRANSFORMERS.get(endpoint, _passthrough_with_model)
    return transformer(body, backend)
