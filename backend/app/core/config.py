from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CHOAM API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/choam"
    cors_origins: list[str] = ["http://localhost:3000"]
    log_level: str = "INFO"
    paypal_client_id: str | None = None
    paypal_client_secret: str | None = None
    paypal_base_url: str = "https://api-m.sandbox.paypal.com"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
