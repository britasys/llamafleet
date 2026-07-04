import pytest

from app.core.config import (
    AppConfig,
    AuthConfig,
    BackendConfig,
    LoggingConfig,
    RoutingConfig,
    RoutingRule,
    ServerConfig,
)


def make_backend(name, model, prompt_name=None, rag_name=None, priority=100, tags=None):
    return BackendConfig(
        name=name,
        url=f"http://{name}:9000",
        model=model,
        prompt_name=prompt_name,
        rag_name=rag_name,
        priority=priority,
        tags=tags or [],
    )


@pytest.fixture
def base_config():
    backends = [
        make_backend("llama-fast", "llama-fast",
                     prompt_name="default_prompt", priority=10),
        make_backend("backend-with-rag", "llama-fast",
                     prompt_name="default_prompt", priority=40),
        make_backend("qwen-tools", "qwen-tools",
                     prompt_name="default_prompt", priority=20),
        make_backend("embeddings", "embeddings",
                     prompt_name="default_prompt", priority=30),
    ]
    routing = RoutingConfig(
        default_backend="llama-fast",
        rules=[
            RoutingRule(name="embeddings",
                        endpoint="/v1/embeddings", backend="embeddings"),
            RoutingRule(name="tools", requires_tools=True,
                        backend="qwen-tools"),
        ],
    )
    return AppConfig(
        server=ServerConfig(),
        auth=AuthConfig(enabled=False),
        prompts={"default_prompt": "You are a helpful assistant."},
        rags=[],
        backends=backends,
        routing=routing,
        logging=LoggingConfig(),
    )
