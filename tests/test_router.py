from app.core.config import AppConfig
from app.services.router import RouterService


def make_config():
    return AppConfig.model_validate(
        {
            "backends": [
                {"name": "default", "url": "http://localhost:8081", "model": "default"},
                {"name": "tools", "url": "http://localhost:8082", "model": "tools"},
                {"name": "embeddings", "url": "http://localhost:8083", "model": "embeddings"},
            ],
            "routing": {
                "default_backend": "default",
                "rules": [
                    {"name": "embeddings", "endpoint": "/v1/embeddings", "backend": "embeddings"},
                    {"name": "tools", "requires_tools": True, "backend": "tools"},
                ],
            },
        }
    )


def test_default_route():
    router = RouterService(make_config())
    backend = router.get_backend("/v1/chat/completions", {"model": "auto"})
    assert backend.name == "default"


def test_tools_route():
    router = RouterService(make_config())
    backend = router.get_backend("/v1/chat/completions", {"model": "auto", "tools": [{"type": "function"}]})
    assert backend.name == "tools"


def test_embeddings_route():
    router = RouterService(make_config())
    backend = router.get_backend("/v1/embeddings", {"model": "auto", "input": "hello"})
    assert backend.name == "embeddings"
