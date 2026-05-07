from functools import lru_cache
from pathlib import Path

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE_PATH = REPO_ROOT / ".env"
PRODUCTION_ENVIRONMENTS = {"prod", "production"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="Bitcoin Bastion", alias="APP_NAME")
    environment: str = Field(default="dev", alias="ENVIRONMENT")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")

    database_url: str = Field(
        default="sqlite+pysqlite:///./bitcoin_bastion.db", alias="DATABASE_URL"
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_default_chat_id: str = Field(default="", alias="TELEGRAM_DEFAULT_CHAT_ID")
    admin_chat_ids: str = Field(default="", alias="ADMIN_CHAT_IDS")
    bot_api_base_url: str = Field(default="http://localhost:8000", alias="BOT_API_BASE_URL")
    bot_api_bearer_token: str = Field(default="", alias="BOT_API_BEARER_TOKEN")

    jwt_secret_key: str = Field(default="change-me-in-prod", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")

    rate_limit_per_minute: int = Field(default=120, alias="RATE_LIMIT_PER_MINUTE")

    news_fetch_interval_seconds: int = Field(default=300, alias="NEWS_FETCH_INTERVAL_SECONDS")
    onchain_large_transfer_sats: int = Field(
        default=1_000_000_000, alias="ONCHAIN_LARGE_TRANSFER_SATS"
    )
    bitcoin_esplora_url: str = Field(default="", alias="BITCOIN_ESPLORA_URL")
    bitcoin_provider_timeout_seconds: float = Field(
        default=6.0, alias="BITCOIN_PROVIDER_TIMEOUT_SECONDS"
    )
    delivery_max_failed_attempts_per_signal_destination: int = Field(
        default=5, alias="DELIVERY_MAX_FAILED_ATTEMPTS_PER_SIGNAL_DESTINATION"
    )
    delivery_retry_cooldown_seconds: int = Field(
        default=300, alias="DELIVERY_RETRY_COOLDOWN_SECONDS"
    )
    citadel_score_weights_json: str = Field(default="", alias="CITADEL_SCORE_WEIGHTS_JSON")
    citadel_external_signal_factors_json: str = Field(
        default="", alias="CITADEL_EXTERNAL_SIGNAL_FACTORS_JSON"
    )

    @model_validator(mode="after")
    def validate_production_secret_guards(self) -> "Settings":
        if self.environment.lower() not in PRODUCTION_ENVIRONMENTS:
            return self

        weak_secret_values = {
            "",
            "change-me-in-prod",
            "changeme",
            "default",
            "secret",
            "insecure",
        }
        secret = self.jwt_secret_key.strip()
        if secret.lower() in weak_secret_values or len(secret) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be non-default and at least 32 characters in production."
            )

        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
