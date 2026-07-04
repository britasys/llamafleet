import pytest

from app.services.router import RouterService


def test_default_backend_used_when_no_rule_matches(base_config):
    router = RouterService(base_config)
    backend = router.get_backend("/v1/chat/completions", {})
    assert backend.name == "llama-fast"


def test_endpoint_rule_matches(base_config):
    router = RouterService(base_config)
    backend = router.get_backend("/v1/embeddings", {})
    assert backend.name == "embeddings"


def test_requires_tools_rule_matches(base_config):
    router = RouterService(base_config)
    backend = router.get_backend(
        "/v1/chat/completions", {"tools": [{"name": "search"}]})
    assert backend.name == "qwen-tools"


def test_unknown_default_backend_raises():
    from app.core.config import AppConfig, AuthConfig, BackendConfig, LoggingConfig, RoutingConfig, ServerConfig

    with pytest.raises(ValueError):
        AppConfig(
            server=ServerConfig(),
            auth=AuthConfig(enabled=False),
            prompts={"default_prompt": "hi"},
            rags=[],
            backends=[BackendConfig(
                name="a", url="http://a", model="m", prompt_name="default_prompt")],
            routing=RoutingConfig(default_backend="does-not-exist"),
            logging=LoggingConfig(),
        )


def test_get_backends_groups_by_model(base_config):
    router = RouterService(base_config)
    candidates = router.get_backends("/v1/chat/completions", {})
    names = {b.name for b in candidates}
    assert names == {"llama-fast", "backend-with-rag"}


def test_get_backends_falls_back_to_primary_when_alone(base_config):
    router = RouterService(base_config)
    candidates = router.get_backends("/v1/embeddings", {})
    assert [b.name for b in candidates] == ["embeddings"]
