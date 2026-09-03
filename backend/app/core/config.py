from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "CommunityAI API"
    api_v1_prefix: str = "/api/v1"
    backend_cors_origins: str = Field(
        default="http://localhost:5173",
        alias="BACKEND_CORS_ORIGINS",
    )

    postgres_db: str = Field(default="communityai", alias="POSTGRES_DB")
    postgres_user: str = Field(default="communityai", alias="POSTGRES_USER")
    postgres_password: str = Field(default="communityai", alias="POSTGRES_PASSWORD")
    postgres_host: str = Field(default="postgres", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")

    jwt_secret_key: str = Field(default="change-me-in-dev", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        alias="REFRESH_TOKEN_EXPIRE_DAYS",
    )
    refresh_cookie_name: str = Field(default="refresh_token", alias="REFRESH_COOKIE_NAME")
    refresh_cookie_secure: bool = Field(default=False, alias="REFRESH_COOKIE_SECURE")
    refresh_cookie_samesite: str = Field(default="lax", alias="REFRESH_COOKIE_SAMESITE")
    refresh_cookie_path: str = Field(default="/api/v1/auth", alias="REFRESH_COOKIE_PATH")

    meta_client_id: str | None = Field(default=None, alias="META_CLIENT_ID")
    meta_client_secret: str | None = Field(default=None, alias="META_CLIENT_SECRET")
    meta_redirect_uri: str | None = Field(default=None, alias="META_REDIRECT_URI")

    linkedin_client_id: str | None = Field(default=None, alias="LINKEDIN_CLIENT_ID")
    linkedin_client_secret: str | None = Field(default=None, alias="LINKEDIN_CLIENT_SECRET")
    linkedin_redirect_uri: str | None = Field(default=None, alias="LINKEDIN_REDIRECT_URI")

    social_token_encryption_key: str | None = Field(default=None, alias="SOCIAL_TOKEN_ENCRYPTION_KEY")
    social_mock_mode: bool = Field(default=False, alias="SOCIAL_MOCK_MODE")

    ai_provider: str = Field(default="mock", alias="AI_PROVIDER")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-1.5-flash", alias="GEMINI_MODEL")

    redis_host: str = Field(default="redis", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")


    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def database_url(self) -> str:
        return (
            "postgresql+psycopg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
