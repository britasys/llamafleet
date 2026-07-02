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


class BackendConfig(BaseModel):
    name: str
    url: str
    model: str
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
    backends: list[BackendConfig]
    routing: RoutingConfig
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


class Settings(BaseSettings):
    llama_gateway_config: str = "config.yaml"


def load_yaml(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    return data


@lru_cache
def get_config() -> AppConfig:
    settings = Settings()
    return AppConfig.model_validate(load_yaml(settings.llama_gateway_config))
