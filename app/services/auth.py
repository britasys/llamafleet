from fastapi import Request

from app.core.config import AppConfig
from app.core.errors import unauthorized


class AuthService:
    def __init__(self, config: AppConfig):
        self.config = config

    def verify(self, request: Request) -> None:
        if not self.config.auth.enabled:
            return

        authorization = request.headers.get("authorization", "")
        x_api_key = request.headers.get("x-api-key", "")
        token = ""

        if authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
        elif x_api_key:
            token = x_api_key.strip()

        if token not in self.config.auth.api_keys:
            raise unauthorized()
