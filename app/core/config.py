from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ServerConfig(BaseModel):
    name: str = "llama-gateway"
    host: str = "0.0.0.0"
    port: int = 4000
    request_timeout_seconds: float = 300


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


class Settings(BaseSettings):
    llama_gateway_config: str = "config.example.yaml"


def resolve_prompt(prompts: dict[str, str], backend: BackendConfig) -> str:
    return prompts.get(
        backend.prompt or "default_prompt",
        prompts["default_prompt"]
    )

def resolve_rag(rags: list[RAGConfig], backend: BackendConfig) -> RAGConfig | None:
    if backend.rag_name is None:
        return None
    for rag in rags:
        if rag.name == backend.rag_name:
            return rag
    return None

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
    return AppConfig.model_validate(load_yaml(settings.llama_gateway_config))
