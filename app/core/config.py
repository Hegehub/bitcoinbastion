from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator, model_validator
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


    cors_allow_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"], alias="CORS_ALLOW_ORIGINS"
    )

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
    jwt_issuer: str = Field(default="bitcoin-bastion", alias="JWT_ISSUER")
    jwt_access_token_expires_minutes: int = Field(default=60, ge=5, le=24 * 60, alias="JWT_ACCESS_TOKEN_EXPIRES_MINUTES")

    rate_limit_per_minute: int = Field(default=120, alias="RATE_LIMIT_PER_MINUTE")

    news_fetch_interval_seconds: int = Field(default=300, alias="NEWS_FETCH_INTERVAL_SECONDS")
    news_ingestion_enabled: bool = Field(default=True, alias="NEWS_INGESTION_ENABLED")
    news_fetch_timeout_seconds: int = Field(default=10, alias="NEWS_FETCH_TIMEOUT_SECONDS")
    news_fetch_max_retries: int = Field(default=3, alias="NEWS_FETCH_MAX_RETRIES")
    news_max_payload_mb: int = Field(default=4, alias="NEWS_MAX_PAYLOAD_MB")
    news_user_agent: str = Field(default="BitcoinBastionNews/1.0", alias="NEWS_USER_AGENT")

    market_flat_threshold_pct: float = Field(default=0.05, alias="MARKET_FLAT_THRESHOLD_PCT")
    news_impact_min_provider_confidence: float = Field(default=0.4, alias="NEWS_IMPACT_MIN_PROVIDER_CONFIDENCE")
    news_impact_default_volatility: float = Field(default=0.02, alias="NEWS_IMPACT_DEFAULT_VOLATILITY")
    news_impact_degraded_confidence_multiplier: float = Field(default=0.8, alias="NEWS_IMPACT_DEGRADED_CONFIDENCE_MULTIPLIER")
    news_impact_windows_minutes: str = Field(default="15,60,240,1440", alias="NEWS_IMPACT_WINDOWS_MINUTES")
    news_impact_nearest_price_tolerance_minutes: int = Field(default=10, alias="NEWS_IMPACT_NEAREST_PRICE_TOLERANCE_MINUTES")
    attribution_window_before_minutes: int = Field(default=240, alias="ATTRIBUTION_WINDOW_BEFORE_MINUTES")
    attribution_window_after_minutes: int = Field(default=15, alias="ATTRIBUTION_WINDOW_AFTER_MINUTES")
    attribution_top_candidates: int = Field(default=5, alias="ATTRIBUTION_TOP_CANDIDATES")
    attribution_max_confidence: float = Field(default=0.92, alias="ATTRIBUTION_MAX_CONFIDENCE")
    attribution_enable_replay: bool = Field(default=True, alias="ATTRIBUTION_ENABLE_REPLAY")
    attribution_window_config_json: str = Field(
        default='{"15m":{"before":45,"after":15},"1h":{"before":240,"after":60},"4h":{"before":720,"after":240},"1d":{"before":2880,"after":720}}',
        alias="ATTRIBUTION_WINDOW_CONFIG_JSON",
    )
    attribution_ranking_weights_json: str = Field(
        default='{"btc_relevance_score":0.18,"market_impact_score":0.16,"source_credibility_score":0.12,"impact_confidence":0.12,"historical_similarity_score":0.08,"pattern_match_score":0.08,"provider_confidence":0.10,"time_distance":0.08,"direction_match":0.05,"volatility_weight":0.03}',
        alias="ATTRIBUTION_RANKING_WEIGHTS_JSON",
    )
    attribution_time_decay_half_life_minutes: int = Field(
        default=120, alias="ATTRIBUTION_TIME_DECAY_HALF_LIFE_MINUTES"
    )
    attribution_low_confidence_threshold: float = Field(
        default=0.35, alias="ATTRIBUTION_LOW_CONFIDENCE_THRESHOLD"
    )
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
    webhook_dispatch_enabled: bool = Field(default=True, alias="WEBHOOK_DISPATCH_ENABLED")
    webhook_dispatch_batch_size: int = Field(default=50, ge=1, le=500, alias="WEBHOOK_DISPATCH_BATCH_SIZE")
    webhook_dispatch_timeout_seconds: float = Field(default=5.0, ge=1.0, le=30.0, validation_alias=AliasChoices("WEBHOOK_DISPATCH_TIMEOUT_SECONDS", "BB_WEBHOOK_TIMEOUT_SECONDS"))
    webhook_dispatch_max_attempts: int = Field(default=5, ge=1, le=25, validation_alias=AliasChoices("WEBHOOK_DISPATCH_MAX_ATTEMPTS", "BB_WEBHOOK_MAX_ATTEMPTS"))
    webhook_dispatch_initial_retry_seconds: int = Field(default=30, ge=1, le=3600, alias="WEBHOOK_DISPATCH_INITIAL_RETRY_SECONDS")
    webhook_dispatch_max_retry_seconds: int = Field(default=3600, ge=1, le=86400, validation_alias=AliasChoices("WEBHOOK_DISPATCH_MAX_RETRY_SECONDS", "BB_WEBHOOK_MAX_RETRY_SECONDS"))
    webhook_dispatch_response_preview_bytes: int = Field(default=2048, ge=128, le=8192, alias="WEBHOOK_DISPATCH_RESPONSE_PREVIEW_BYTES")
    webhook_max_payload_bytes: int = Field(default=65_536, ge=1024, le=1_000_000, alias="BB_WEBHOOK_MAX_PAYLOAD_BYTES")
    webhook_signature_tolerance_seconds: int = Field(default=300, ge=30, le=3600, alias="BB_WEBHOOK_SIGNATURE_TOLERANCE_SECONDS")
    webhook_allow_private_network_targets: bool = Field(default=False, alias="BB_WEBHOOK_ALLOW_PRIVATE_NETWORK_TARGETS")
    ws_max_topics_per_connection: int = Field(default=8, ge=1, le=32, alias="BB_WS_MAX_TOPICS_PER_CONNECTION")
    ws_max_payload_bytes: int = Field(default=65_536, ge=1024, le=1_000_000, alias="BB_WS_MAX_PAYLOAD_BYTES")
    events_max_payload_bytes: int = Field(default=65_536, ge=1024, le=1_000_000, alias="BB_EVENTS_MAX_PAYLOAD_BYTES")
    events_max_metadata_bytes: int = Field(default=16_384, ge=1024, le=1_000_000, alias="BB_EVENTS_MAX_METADATA_BYTES")
    citadel_score_weights_json: str = Field(default="", alias="CITADEL_SCORE_WEIGHTS_JSON")
    citadel_external_signal_factors_json: str = Field(
        default="", alias="CITADEL_EXTERNAL_SIGNAL_FACTORS_JSON"
    )


    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def parse_cors_allow_origins(cls, value: object) -> list[str]:
        if value is None:
            return ["http://localhost:3000"]
        if isinstance(value, str):
            origins = [item.strip() for item in value.split(",") if item.strip()]
            return origins or ["http://localhost:3000"]
        if isinstance(value, (list, tuple, set)):
            origins = [str(item).strip() for item in value if str(item).strip()]
            return origins or ["http://localhost:3000"]
        raise ValueError("CORS_ALLOW_ORIGINS must be a comma-separated string or list of origins.")

    @model_validator(mode="after")
    def validate_production_secret_guards(self) -> "Settings":
        if "*" in self.cors_allow_origins:
            raise ValueError("CORS_ALLOW_ORIGINS cannot include wildcard '*'.")

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

        if self.jwt_algorithm != "HS256":
            raise ValueError("JWT_ALGORITHM must remain HS256 unless explicit cryptographic review is completed.")

        if not self.jwt_issuer.strip():
            raise ValueError("JWT_ISSUER must be set in production.")

        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
