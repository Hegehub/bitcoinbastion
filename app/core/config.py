from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="Bitcoin Bastion", alias="APP_NAME")
    environment: str = Field(default="dev", alias="ENVIRONMENT")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")

    database_url: str = Field(default="sqlite+pysqlite:///./bitcoin_bastion.db", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_default_chat_id: str = Field(default="", alias="TELEGRAM_DEFAULT_CHAT_ID")
    admin_chat_ids: str = Field(default="", alias="ADMIN_CHAT_IDS")

    news_fetch_interval_seconds: int = Field(default=300, alias="NEWS_FETCH_INTERVAL_SECONDS")
    onchain_large_transfer_sats: int = Field(default=1_000_000_000, alias="ONCHAIN_LARGE_TRANSFER_SATS")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
