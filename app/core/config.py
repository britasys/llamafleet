from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings


class ServerConfig(BaseModel):
    name: str = "llama-gateway"
    host: str = "0.0.0.0"
    port: int = 4000
    request_timeout_seconds: float = 300
    max_concurrent_requests: int = 64
    max_queue_size: int = 500
    queue_timeout_seconds: float = 30
    rate_limit_capacity: float = 60
    rate_limit_refill_per_second: float = 1.0


class AuthConfig(BaseModel):
    enabled: bool = True
    api_keys: list[str] = Field(default_factory=list)


class RAGConfig(BaseModel):
    name: str
    url: str
    type: str
    collection: str
    top_k: int = 5
    min_score: float = 0.0


class BackendConfig(BaseModel):
    name: str
    url: str
    model: str
    rag_name: str | None = None
    rag: RAGConfig | None = None
    prompt_name: str | None = None
    prompt: str | None = None
    messages: list[str] | None = None
    tags: list[str] = Field(default_factory=list)
    priority: int = 100


class RoutingRule(BaseModel):
    name: str
    endpoint: str | None = None
    model: str | None = None
    requires_tools: bool | None = None
    backend: str


class RoutingConfig(BaseModel):
    default_backend: str
    rules: list[RoutingRule] = Field(default_factory=list)


class LoggingConfig(BaseModel):
    enabled: bool = True


class AppConfig(BaseModel):
    server: ServerConfig = Field(default_factory=ServerConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    prompts: dict[str, str] = Field(default_factory=dict)
    rags: list[RAGConfig] = Field(default_factory=list)
    backends: list[BackendConfig]
    routing: RoutingConfig
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @model_validator(mode="after")
    def _validate_references(self) -> "AppConfig":
        if not self.backends:
            raise ValueError("config must define at least one backend")

        backend_names = [backend.name for backend in self.backends]
        duplicates = {
            name for name in backend_names if backend_names.count(name) > 1}
        if duplicates:
            raise ValueError(
                f"duplicate backend names in config: {sorted(duplicates)}")

        name_set = set(backend_names)
        rag_names = {rag.name for rag in self.rags}

        if self.routing.default_backend not in name_set:
            raise ValueError(
                f"routing.default_backend '{self.routing.default_backend}' "
                f"is not a defined backend: {sorted(name_set)}"
            )

        for rule in self.routing.rules:
            if rule.backend not in name_set:
                raise ValueError(
                    f"routing rule '{rule.name}' points to unknown backend '{rule.backend}'"
                )

        for backend in self.backends:
            if backend.rag_name is not None and backend.rag_name not in rag_names:
                raise ValueError(
                    f"backend '{backend.name}' references unknown rag '{backend.rag_name}'"
                )
            if backend.prompt_name is not None and backend.prompt_name not in self.prompts:
                raise ValueError(
                    f"backend '{backend.name}' references unknown prompt '{backend.prompt_name}'"
                )

        return self


class Settings(BaseSettings):
    llama_gateway_config: str = "config.example.yaml"


def resolve_prompt(prompts: dict[str, str], backend: BackendConfig) -> str:
    prompt_name = backend.prompt_name or "default_prompt"
    if prompt_name not in prompts:
        raise ValueError(
            f"backend '{backend.name}' references unknown prompt '{prompt_name}'")
    return prompts[prompt_name]


def resolve_rag(rags: list[RAGConfig], backend: BackendConfig) -> RAGConfig | None:
    if backend.rag_name is None:
        return None
    for rag in rags:
        if rag.name == backend.rag_name:
            return rag
    raise ValueError(
        f"backend '{backend.name}' references unknown rag '{backend.rag_name}'")


def load_yaml(path: str | Path) -> AppConfig:
    with open(path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    config = AppConfig.model_validate(data)

    for backend in config.backends:
        backend.prompt = resolve_prompt(config.prompts, backend)
        backend.rag = resolve_rag(config.rags, backend)

    return config


@lru_cache
def get_config() -> AppConfig:
    settings = Settings()
    return load_yaml(settings.llama_gateway_config)
