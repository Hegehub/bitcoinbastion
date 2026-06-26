from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE_PATH = REPO_ROOT / ".env"
PRODUCTION_ENVIRONMENTS = {"prod", "production"}
PRODUCTION_STORAGE_PROFILES = {"production", "staging", "enterprise", "air_gapped"}

StorageProfile = Literal[
    "development",
    "test",
    "single_node",
    "self_hosted",
    "staging",
    "production",
    "enterprise",
    "air_gapped",
]
ObjectStorageProvider = Literal["disabled", "local", "minio", "s3", "compatible_s3"]
VectorStoreProvider = Literal["disabled", "pgvector", "qdrant"]
ClickHouseProfile = Literal[
    "disabled",
    "development",
    "single_node",
    "staging",
    "production",
    "enterprise",
]


@dataclass(frozen=True)
class PostgresStorageSettings:
    database_url: str
    postgres_url: str
    read_replica_url: str
    ssl_mode: str
    pool_size: int
    max_overflow: int
    pool_timeout_seconds: int
    statement_timeout_ms: int

    @property
    def effective_url(self) -> str:
        return self.postgres_url or self.database_url


@dataclass(frozen=True)
class RedisStorageSettings:
    url: str
    tls_enabled: bool
    key_prefix: str
    ephemeral_only: bool


@dataclass(frozen=True)
class ObjectStorageSettings:
    enabled: bool
    backend: ObjectStorageProvider
    provider: ObjectStorageProvider
    endpoint: str
    public_endpoint: str
    bucket: str
    region: str
    access_key: str
    secret_key: str
    use_ssl: bool
    force_path_style: bool
    default_retention_days: int
    evidence_retention_days: int
    worm_enabled: bool
    checksum_required: bool
    local_root: str
    max_object_bytes: int


@dataclass(frozen=True)
class TimescaleStorageSettings:
    enabled: bool
    url: str
    create_extension: bool
    schema: str
    default_chunk_interval: str
    health_timeout_seconds: int
    retention_days: int | None
    retention_enabled: bool
    raw_market_retention_days: int
    raw_health_retention_days: int
    raw_usage_retention_days: int
    aggregate_retention_days: int
    access_history_retention_days: int
    compression_enabled: bool
    compress_after_days: int
    compress_market_after_days: int
    compress_health_after_days: int
    compress_usage_after_days: int
    continuous_aggregates_enabled: bool


@dataclass(frozen=True)
class ClickHouseStorageSettings:
    enabled: bool
    url: str
    host: str
    port: int
    database: str
    username: str
    password: str
    secure: bool
    connect_timeout_seconds: int
    query_timeout_seconds: int
    insert_timeout_seconds: int
    max_retries: int
    profile: ClickHouseProfile
    projection_lag_warn_seconds: int
    projection_lag_critical_seconds: int


@dataclass(frozen=True)
class VectorStorageSettings:
    provider: VectorStoreProvider
    qdrant_enabled: bool
    qdrant_url: str
    qdrant_api_key: str
    qdrant_collection_prefix: str
    pgvector_enabled: bool
    embedding_model_version: str
    redaction_required: bool


@dataclass(frozen=True)
class LocalStorageSettings:
    enabled: bool
    sqlite_path: str
    duckdb_path: str
    encryption_required: bool
    sync_log_enabled: bool


@dataclass(frozen=True)
class StorageHealthSettings:
    enabled: bool
    degraded_mode_enabled: bool
    fail_fast_on_critical_missing: bool
    require_object_storage_in_production: bool
    require_backup_evidence_in_production: bool


@dataclass(frozen=True)
class StorageSettings:
    profile: StorageProfile
    postgres: PostgresStorageSettings
    redis: RedisStorageSettings
    object_storage: ObjectStorageSettings
    timescale: TimescaleStorageSettings
    clickhouse: ClickHouseStorageSettings
    vector: VectorStorageSettings
    local: LocalStorageSettings
    health: StorageHealthSettings


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
    storage_profile: StorageProfile = Field(default="development", alias="STORAGE_PROFILE")

    postgres_url: str = Field(default="", alias="POSTGRES_URL")
    postgres_read_replica_url: str = Field(default="", alias="POSTGRES_READ_REPLICA_URL")
    postgres_ssl_mode: str = Field(default="prefer", alias="POSTGRES_SSL_MODE")
    postgres_pool_size: int = Field(default=5, ge=1, alias="POSTGRES_POOL_SIZE")
    postgres_max_overflow: int = Field(default=10, ge=0, alias="POSTGRES_MAX_OVERFLOW")
    postgres_pool_timeout_seconds: int = Field(
        default=30, ge=1, alias="POSTGRES_POOL_TIMEOUT_SECONDS"
    )
    postgres_statement_timeout_ms: int = Field(
        default=30_000, ge=0, alias="POSTGRES_STATEMENT_TIMEOUT_MS"
    )

    # Redis is cache/queue/rate-limit/websocket infrastructure only; it is not durable truth.
    redis_tls_enabled: bool = Field(default=False, alias="REDIS_TLS_ENABLED")
    redis_key_prefix: str = Field(default="bitcoin_bastion", alias="REDIS_KEY_PREFIX")
    redis_ephemeral_only: bool = Field(default=True, alias="REDIS_EPHEMERAL_ONLY")

    object_storage_enabled: bool = Field(default=False, alias="OBJECT_STORAGE_ENABLED")
    object_storage_provider: ObjectStorageProvider = Field(
        default="disabled", alias="OBJECT_STORAGE_PROVIDER"
    )
    object_storage_backend: ObjectStorageProvider = Field(
        default="disabled", alias="OBJECT_STORAGE_BACKEND"
    )
    object_storage_endpoint: str = Field(default="", alias="OBJECT_STORAGE_ENDPOINT")
    object_storage_public_endpoint: str = Field(default="", alias="OBJECT_STORAGE_PUBLIC_ENDPOINT")
    object_storage_bucket: str = Field(default="", alias="OBJECT_STORAGE_BUCKET")
    object_storage_region: str = Field(default="", alias="OBJECT_STORAGE_REGION")
    object_storage_access_key: str = Field(default="", alias="OBJECT_STORAGE_ACCESS_KEY")
    object_storage_secret_key: str = Field(default="", alias="OBJECT_STORAGE_SECRET_KEY")
    object_storage_use_ssl: bool = Field(default=True, alias="OBJECT_STORAGE_USE_SSL")
    object_storage_secure: bool = Field(default=True, alias="OBJECT_STORAGE_SECURE")
    object_storage_force_path_style: bool = Field(
        default=True, alias="OBJECT_STORAGE_FORCE_PATH_STYLE"
    )
    object_storage_default_retention_days: int = Field(
        default=90, ge=0, alias="OBJECT_STORAGE_DEFAULT_RETENTION_DAYS"
    )
    object_storage_evidence_retention_days: int = Field(
        default=2555, ge=0, alias="OBJECT_STORAGE_EVIDENCE_RETENTION_DAYS"
    )
    object_storage_worm_enabled: bool = Field(default=False, alias="OBJECT_STORAGE_WORM_ENABLED")
    object_storage_checksum_required: bool = Field(
        default=True, alias="OBJECT_STORAGE_CHECKSUM_REQUIRED"
    )
    object_storage_local_root: str = Field(
        default=".storage/objects", alias="OBJECT_STORAGE_LOCAL_ROOT"
    )
    object_storage_max_object_bytes: int = Field(
        default=100 * 1024 * 1024,
        ge=1,
        validation_alias=AliasChoices(
            "OBJECT_STORAGE_MAX_OBJECT_BYTES", "OBJECT_STORAGE_MAX_ARTIFACT_BYTES"
        ),
    )

    timescale_enabled: bool = Field(default=False, alias="TIMESCALE_ENABLED")
    timescale_url: str = Field(default="", alias="TIMESCALE_URL")
    timescale_create_extension: bool = Field(default=False, alias="TIMESCALE_CREATE_EXTENSION")
    timescale_schema: str = Field(default="public", alias="TIMESCALE_SCHEMA")
    timescale_default_chunk_interval: str = Field(
        default="1 day", alias="TIMESCALE_DEFAULT_CHUNK_INTERVAL"
    )
    timescale_health_timeout_seconds: int = Field(
        default=2, ge=1, alias="TIMESCALE_HEALTH_TIMEOUT_SECONDS"
    )
    timescale_retention_days: int | None = Field(default=None, alias="TIMESCALE_RETENTION_DAYS")
    timescale_retention_enabled: bool = Field(default=True, alias="TIMESCALE_RETENTION_ENABLED")
    timescale_raw_market_retention_days: int = Field(
        default=180, ge=1, alias="TIMESCALE_RAW_MARKET_RETENTION_DAYS"
    )
    timescale_raw_health_retention_days: int = Field(
        default=90, ge=1, alias="TIMESCALE_RAW_HEALTH_RETENTION_DAYS"
    )
    timescale_raw_usage_retention_days: int = Field(
        default=180, ge=1, alias="TIMESCALE_RAW_USAGE_RETENTION_DAYS"
    )
    timescale_aggregate_retention_days: int = Field(
        default=3650, ge=1, alias="TIMESCALE_AGGREGATE_RETENTION_DAYS"
    )
    timescale_access_history_retention_days: int = Field(
        default=730, ge=1, alias="TIMESCALE_ACCESS_HISTORY_RETENTION_DAYS"
    )
    timescale_compression_enabled: bool = Field(default=True, alias="TIMESCALE_COMPRESSION_ENABLED")
    timescale_compress_after_days: int = Field(
        default=7, ge=1, alias="TIMESCALE_COMPRESS_AFTER_DAYS"
    )
    timescale_compress_market_after_days: int = Field(
        default=7, ge=1, alias="TIMESCALE_COMPRESS_MARKET_AFTER_DAYS"
    )
    timescale_compress_health_after_days: int = Field(
        default=14, ge=1, alias="TIMESCALE_COMPRESS_HEALTH_AFTER_DAYS"
    )
    timescale_compress_usage_after_days: int = Field(
        default=14, ge=1, alias="TIMESCALE_COMPRESS_USAGE_AFTER_DAYS"
    )
    timescale_continuous_aggregates_enabled: bool = Field(
        default=True, alias="TIMESCALE_CONTINUOUS_AGGREGATES_ENABLED"
    )

    clickhouse_enabled: bool = Field(default=False, alias="CLICKHOUSE_ENABLED")
    clickhouse_url: str = Field(default="http://localhost:8123", alias="CLICKHOUSE_URL")
    clickhouse_host: str = Field(default="localhost", alias="CLICKHOUSE_HOST")
    clickhouse_port: int = Field(default=8123, ge=1, le=65535, alias="CLICKHOUSE_PORT")
    clickhouse_database: str = Field(default="bitcoin_bastion", alias="CLICKHOUSE_DATABASE")
    clickhouse_username: str = Field(
        default="default", validation_alias=AliasChoices("CLICKHOUSE_USERNAME", "CLICKHOUSE_USER")
    )
    clickhouse_password: str = Field(default="", alias="CLICKHOUSE_PASSWORD")
    clickhouse_secure: bool = Field(default=False, alias="CLICKHOUSE_SECURE")
    clickhouse_connect_timeout_seconds: int = Field(
        default=5, ge=1, alias="CLICKHOUSE_CONNECT_TIMEOUT_SECONDS"
    )
    clickhouse_query_timeout_seconds: int = Field(
        default=15, ge=1, alias="CLICKHOUSE_QUERY_TIMEOUT_SECONDS"
    )
    clickhouse_insert_timeout_seconds: int = Field(
        default=30, ge=1, alias="CLICKHOUSE_INSERT_TIMEOUT_SECONDS"
    )
    clickhouse_max_retries: int = Field(default=2, ge=0, alias="CLICKHOUSE_MAX_RETRIES")
    clickhouse_profile: ClickHouseProfile = Field(default="disabled", alias="CLICKHOUSE_PROFILE")
    clickhouse_projection_lag_warn_seconds: int = Field(
        default=300, ge=1, alias="CLICKHOUSE_PROJECTION_LAG_WARN_SECONDS"
    )
    clickhouse_projection_lag_critical_seconds: int = Field(
        default=900, ge=1, alias="CLICKHOUSE_PROJECTION_LAG_CRITICAL_SECONDS"
    )

    vector_store_provider: VectorStoreProvider = Field(
        default="disabled", alias="VECTOR_STORE_PROVIDER"
    )
    qdrant_enabled: bool = Field(default=False, alias="QDRANT_ENABLED")
    qdrant_url: str = Field(default="", alias="QDRANT_URL")
    qdrant_api_key: str = Field(default="", alias="QDRANT_API_KEY")
    qdrant_collection_prefix: str = Field(
        default="bitcoin_bastion", alias="QDRANT_COLLECTION_PREFIX"
    )
    pgvector_enabled: bool = Field(default=False, alias="PGVECTOR_ENABLED")
    embedding_model_version: str = Field(default="", alias="EMBEDDING_MODEL_VERSION")
    vector_redaction_required: bool = Field(default=True, alias="VECTOR_REDACTION_REQUIRED")

    local_storage_enabled: bool = Field(default=False, alias="LOCAL_STORAGE_ENABLED")
    local_sqlite_path: str = Field(
        default="./data/local/bastion.sqlite3", alias="LOCAL_SQLITE_PATH"
    )
    local_duckdb_path: str = Field(default="./data/local/bastion.duckdb", alias="LOCAL_DUCKDB_PATH")
    local_storage_encryption_required: bool = Field(
        default=True, alias="LOCAL_STORAGE_ENCRYPTION_REQUIRED"
    )
    local_sync_log_enabled: bool = Field(default=True, alias="LOCAL_SYNC_LOG_ENABLED")

    storage_health_enabled: bool = Field(default=True, alias="STORAGE_HEALTH_ENABLED")
    storage_degraded_mode_enabled: bool = Field(default=True, alias="STORAGE_DEGRADED_MODE_ENABLED")
    storage_fail_fast_on_critical_missing: bool = Field(
        default=True, alias="STORAGE_FAIL_FAST_ON_CRITICAL_MISSING"
    )
    storage_require_object_storage_in_production: bool = Field(
        default=True, alias="STORAGE_REQUIRE_OBJECT_STORAGE_IN_PRODUCTION"
    )
    storage_require_backup_evidence_in_production: bool = Field(
        default=True, alias="STORAGE_REQUIRE_BACKUP_EVIDENCE_IN_PRODUCTION"
    )

    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_default_chat_id: str = Field(default="", alias="TELEGRAM_DEFAULT_CHAT_ID")
    admin_chat_ids: str = Field(default="", alias="ADMIN_CHAT_IDS")
    bot_api_base_url: str = Field(default="http://localhost:8000", alias="BOT_API_BASE_URL")
    bot_api_bearer_token: str = Field(default="", alias="BOT_API_BEARER_TOKEN")

    jwt_secret_key: str = Field(default="change-me-in-prod", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_issuer: str = Field(default="bitcoin-bastion", alias="JWT_ISSUER")
    jwt_access_token_expires_minutes: int = Field(
        default=60, ge=5, le=24 * 60, alias="JWT_ACCESS_TOKEN_EXPIRES_MINUTES"
    )

    rate_limit_per_minute: int = Field(default=120, alias="RATE_LIMIT_PER_MINUTE")

    news_fetch_interval_seconds: int = Field(default=300, alias="NEWS_FETCH_INTERVAL_SECONDS")
    news_ingestion_enabled: bool = Field(default=True, alias="NEWS_INGESTION_ENABLED")
    news_fetch_timeout_seconds: int = Field(default=10, alias="NEWS_FETCH_TIMEOUT_SECONDS")
    news_fetch_max_retries: int = Field(default=3, alias="NEWS_FETCH_MAX_RETRIES")
    news_max_payload_mb: int = Field(default=4, alias="NEWS_MAX_PAYLOAD_MB")
    news_user_agent: str = Field(default="BitcoinBastionNews/1.0", alias="NEWS_USER_AGENT")

    market_flat_threshold_pct: float = Field(default=0.05, alias="MARKET_FLAT_THRESHOLD_PCT")
    news_impact_min_provider_confidence: float = Field(
        default=0.4, alias="NEWS_IMPACT_MIN_PROVIDER_CONFIDENCE"
    )
    news_impact_default_volatility: float = Field(
        default=0.02, alias="NEWS_IMPACT_DEFAULT_VOLATILITY"
    )
    news_impact_degraded_confidence_multiplier: float = Field(
        default=0.8, alias="NEWS_IMPACT_DEGRADED_CONFIDENCE_MULTIPLIER"
    )
    news_impact_windows_minutes: str = Field(
        default="15,60,240,1440", alias="NEWS_IMPACT_WINDOWS_MINUTES"
    )
    news_impact_nearest_price_tolerance_minutes: int = Field(
        default=10, alias="NEWS_IMPACT_NEAREST_PRICE_TOLERANCE_MINUTES"
    )
    attribution_window_before_minutes: int = Field(
        default=240, alias="ATTRIBUTION_WINDOW_BEFORE_MINUTES"
    )
    attribution_window_after_minutes: int = Field(
        default=15, alias="ATTRIBUTION_WINDOW_AFTER_MINUTES"
    )
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
    webhook_dispatch_batch_size: int = Field(
        default=50, ge=1, le=500, alias="WEBHOOK_DISPATCH_BATCH_SIZE"
    )
    webhook_dispatch_timeout_seconds: float = Field(
        default=5.0,
        ge=1.0,
        le=30.0,
        validation_alias=AliasChoices(
            "WEBHOOK_DISPATCH_TIMEOUT_SECONDS", "BB_WEBHOOK_TIMEOUT_SECONDS"
        ),
    )
    webhook_dispatch_max_attempts: int = Field(
        default=5,
        ge=1,
        le=25,
        validation_alias=AliasChoices("WEBHOOK_DISPATCH_MAX_ATTEMPTS", "BB_WEBHOOK_MAX_ATTEMPTS"),
    )
    webhook_dispatch_initial_retry_seconds: int = Field(
        default=30, ge=1, le=3600, alias="WEBHOOK_DISPATCH_INITIAL_RETRY_SECONDS"
    )
    webhook_dispatch_max_retry_seconds: int = Field(
        default=3600,
        ge=1,
        le=86400,
        validation_alias=AliasChoices(
            "WEBHOOK_DISPATCH_MAX_RETRY_SECONDS", "BB_WEBHOOK_MAX_RETRY_SECONDS"
        ),
    )
    webhook_dispatch_response_preview_bytes: int = Field(
        default=2048, ge=128, le=8192, alias="WEBHOOK_DISPATCH_RESPONSE_PREVIEW_BYTES"
    )
    webhook_max_payload_bytes: int = Field(
        default=65_536, ge=1024, le=1_000_000, alias="BB_WEBHOOK_MAX_PAYLOAD_BYTES"
    )
    webhook_signature_tolerance_seconds: int = Field(
        default=300, ge=30, le=3600, alias="BB_WEBHOOK_SIGNATURE_TOLERANCE_SECONDS"
    )
    webhook_allow_private_network_targets: bool = Field(
        default=False, alias="BB_WEBHOOK_ALLOW_PRIVATE_NETWORK_TARGETS"
    )
    ws_max_topics_per_connection: int = Field(
        default=8, ge=1, le=32, alias="BB_WS_MAX_TOPICS_PER_CONNECTION"
    )
    ws_max_payload_bytes: int = Field(
        default=65_536, ge=1024, le=1_000_000, alias="BB_WS_MAX_PAYLOAD_BYTES"
    )
    events_max_payload_bytes: int = Field(
        default=65_536, ge=1024, le=1_000_000, alias="BB_EVENTS_MAX_PAYLOAD_BYTES"
    )
    events_max_metadata_bytes: int = Field(
        default=16_384, ge=1024, le=1_000_000, alias="BB_EVENTS_MAX_METADATA_BYTES"
    )
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
            raise ValueError(
                "JWT_ALGORITHM must remain HS256 unless explicit cryptographic review is completed."
            )

        if not self.jwt_issuer.strip():
            raise ValueError("JWT_ISSUER must be set in production.")

        return self

    @model_validator(mode="after")
    def validate_storage_configuration(self) -> "Settings":
        profile = self.storage_profile
        production_like = profile in PRODUCTION_STORAGE_PROFILES
        postgres_effective_url = self.postgres_url.strip() or self.database_url.strip()

        if production_like:
            if not self.storage_fail_fast_on_critical_missing:
                raise ValueError(
                    "STORAGE_FAIL_FAST_ON_CRITICAL_MISSING must be true in production-like storage profiles."
                )
            if not postgres_effective_url or postgres_effective_url.startswith("sqlite"):
                raise ValueError(
                    "DATABASE_URL or POSTGRES_URL must be set to a PostgreSQL URL in production-like storage profiles."
                )
            if not self.redis_url.strip():
                raise ValueError("REDIS_URL must be set in production-like storage profiles.")

        if (
            profile == "production"
            and self.database_url.strip()
            and self.postgres_url.strip()
            and self.database_url.strip() != self.postgres_url.strip()
        ):
            raise ValueError(
                "DATABASE_URL and POSTGRES_URL must match when both are set in production."
            )

        effective_object_storage_backend = (
            self.object_storage_backend
            if self.object_storage_backend != "disabled"
            else self.object_storage_provider
        )

        if self.object_storage_enabled:
            if effective_object_storage_backend == "disabled":
                raise ValueError(
                    "OBJECT_STORAGE_BACKEND or OBJECT_STORAGE_PROVIDER must not be disabled when OBJECT_STORAGE_ENABLED=true."
                )
            if (
                effective_object_storage_backend != "local"
                and not self.object_storage_bucket.strip()
            ):
                raise ValueError(
                    "OBJECT_STORAGE_BUCKET must be set when object storage is enabled."
                )
            if not self.object_storage_checksum_required:
                raise ValueError(
                    "OBJECT_STORAGE_CHECKSUM_REQUIRED must be true when object storage is enabled."
                )

        if (
            profile == "production"
            and self.storage_require_object_storage_in_production
            and not self.object_storage_enabled
        ):
            raise ValueError(
                "OBJECT_STORAGE_ENABLED must be true when production requires object storage."
            )

        if self.timescale_enabled and (
            self.timescale_retention_days is not None and self.timescale_retention_days <= 0
        ):
            raise ValueError("TIMESCALE_RETENTION_DAYS must be positive when set.")

        if self.timescale_enabled:
            from app.storage.timeseries.errors import TimescaleConfigurationError
            from app.storage.timeseries.hypertables import validate_identifier, validate_interval

            try:
                validate_identifier(self.timescale_schema, label="schema")
                validate_interval(
                    self.timescale_default_chunk_interval, label="default chunk interval"
                )
            except TimescaleConfigurationError as exc:
                raise ValueError(str(exc)) from exc

        if self.clickhouse_enabled:
            if not self.clickhouse_url.strip():
                raise ValueError("CLICKHOUSE_URL must be set when ClickHouse is enabled.")
            if not self.clickhouse_host.strip():
                raise ValueError("CLICKHOUSE_HOST must be set when ClickHouse is enabled.")
            if not self.clickhouse_database.strip():
                raise ValueError("CLICKHOUSE_DATABASE must be set when ClickHouse is enabled.")
            if not self.clickhouse_username.strip():
                raise ValueError("CLICKHOUSE_USERNAME must be set when ClickHouse is enabled.")
            if self.clickhouse_profile == "disabled":
                raise ValueError(
                    "CLICKHOUSE_PROFILE must not be disabled when ClickHouse is enabled."
                )
            if (
                self.clickhouse_projection_lag_warn_seconds
                >= self.clickhouse_projection_lag_critical_seconds
            ):
                raise ValueError(
                    "CLICKHOUSE_PROJECTION_LAG_WARN_SECONDS must be less than "
                    "CLICKHOUSE_PROJECTION_LAG_CRITICAL_SECONDS."
                )
            if production_like:
                weak_clickhouse_passwords = {"", "default", "password", "changeme", "clickhouse"}
                if self.clickhouse_password.strip().lower() in weak_clickhouse_passwords:
                    raise ValueError(
                        "CLICKHOUSE_PASSWORD must be non-placeholder in production-like profiles."
                    )

        if self.vector_store_provider == "qdrant":
            if not self.qdrant_enabled:
                raise ValueError("QDRANT_ENABLED must be true when VECTOR_STORE_PROVIDER=qdrant.")
            if not self.qdrant_url.strip():
                raise ValueError("QDRANT_URL must be set when VECTOR_STORE_PROVIDER=qdrant.")
            if not self.vector_redaction_required:
                raise ValueError("VECTOR_REDACTION_REQUIRED must be true for Qdrant.")

        if self.vector_store_provider == "pgvector":
            if not self.pgvector_enabled:
                raise ValueError(
                    "PGVECTOR_ENABLED must be true when VECTOR_STORE_PROVIDER=pgvector."
                )
            if not self.vector_redaction_required:
                raise ValueError("VECTOR_REDACTION_REQUIRED must be true for pgvector.")

        if production_like and not self.vector_redaction_required:
            raise ValueError(
                "VECTOR_REDACTION_REQUIRED cannot be false in production-like storage profiles."
            )

        if self.local_storage_enabled and production_like:
            if not self.local_storage_encryption_required:
                raise ValueError(
                    "LOCAL_STORAGE_ENCRYPTION_REQUIRED must be true in production-like profiles."
                )
            if not self.local_sync_log_enabled:
                raise ValueError("LOCAL_SYNC_LOG_ENABLED must be true in production-like profiles.")

        return self

    @property
    def storage(self) -> StorageSettings:
        return StorageSettings(
            profile=self.storage_profile,
            postgres=PostgresStorageSettings(
                database_url=self.database_url,
                postgres_url=self.postgres_url,
                read_replica_url=self.postgres_read_replica_url,
                ssl_mode=self.postgres_ssl_mode,
                pool_size=self.postgres_pool_size,
                max_overflow=self.postgres_max_overflow,
                pool_timeout_seconds=self.postgres_pool_timeout_seconds,
                statement_timeout_ms=self.postgres_statement_timeout_ms,
            ),
            redis=RedisStorageSettings(
                url=self.redis_url,
                tls_enabled=self.redis_tls_enabled,
                key_prefix=self.redis_key_prefix,
                ephemeral_only=self.redis_ephemeral_only,
            ),
            object_storage=ObjectStorageSettings(
                enabled=self.object_storage_enabled,
                backend=(
                    self.object_storage_backend
                    if self.object_storage_backend != "disabled"
                    else self.object_storage_provider
                ),
                provider=self.object_storage_provider,
                endpoint=self.object_storage_endpoint,
                public_endpoint=self.object_storage_public_endpoint,
                bucket=self.object_storage_bucket,
                region=self.object_storage_region,
                access_key=self.object_storage_access_key,
                secret_key=self.object_storage_secret_key,
                use_ssl=self.object_storage_use_ssl,
                force_path_style=self.object_storage_force_path_style,
                default_retention_days=self.object_storage_default_retention_days,
                evidence_retention_days=self.object_storage_evidence_retention_days,
                worm_enabled=self.object_storage_worm_enabled,
                checksum_required=self.object_storage_checksum_required,
                local_root=self.object_storage_local_root,
                max_object_bytes=self.object_storage_max_object_bytes,
            ),
            timescale=TimescaleStorageSettings(
                enabled=self.timescale_enabled,
                url=self.timescale_url,
                create_extension=self.timescale_create_extension,
                schema=self.timescale_schema,
                default_chunk_interval=self.timescale_default_chunk_interval,
                health_timeout_seconds=self.timescale_health_timeout_seconds,
                retention_days=self.timescale_retention_days,
                retention_enabled=self.timescale_retention_enabled,
                raw_market_retention_days=self.timescale_raw_market_retention_days,
                raw_health_retention_days=self.timescale_raw_health_retention_days,
                raw_usage_retention_days=self.timescale_raw_usage_retention_days,
                aggregate_retention_days=self.timescale_aggregate_retention_days,
                access_history_retention_days=self.timescale_access_history_retention_days,
                compression_enabled=self.timescale_compression_enabled,
                compress_after_days=self.timescale_compress_after_days,
                compress_market_after_days=self.timescale_compress_market_after_days,
                compress_health_after_days=self.timescale_compress_health_after_days,
                compress_usage_after_days=self.timescale_compress_usage_after_days,
                continuous_aggregates_enabled=self.timescale_continuous_aggregates_enabled,
            ),
            clickhouse=ClickHouseStorageSettings(
                enabled=self.clickhouse_enabled,
                url=self.clickhouse_url,
                host=self.clickhouse_host,
                port=self.clickhouse_port,
                database=self.clickhouse_database,
                username=self.clickhouse_username,
                password=self.clickhouse_password,
                secure=self.clickhouse_secure,
                connect_timeout_seconds=self.clickhouse_connect_timeout_seconds,
                query_timeout_seconds=self.clickhouse_query_timeout_seconds,
                insert_timeout_seconds=self.clickhouse_insert_timeout_seconds,
                max_retries=self.clickhouse_max_retries,
                profile=self.clickhouse_profile,
                projection_lag_warn_seconds=self.clickhouse_projection_lag_warn_seconds,
                projection_lag_critical_seconds=self.clickhouse_projection_lag_critical_seconds,
            ),
            vector=VectorStorageSettings(
                provider=self.vector_store_provider,
                qdrant_enabled=self.qdrant_enabled,
                qdrant_url=self.qdrant_url,
                qdrant_api_key=self.qdrant_api_key,
                qdrant_collection_prefix=self.qdrant_collection_prefix,
                pgvector_enabled=self.pgvector_enabled,
                embedding_model_version=self.embedding_model_version,
                redaction_required=self.vector_redaction_required,
            ),
            local=LocalStorageSettings(
                enabled=self.local_storage_enabled,
                sqlite_path=self.local_sqlite_path,
                duckdb_path=self.local_duckdb_path,
                encryption_required=self.local_storage_encryption_required,
                sync_log_enabled=self.local_sync_log_enabled,
            ),
            health=StorageHealthSettings(
                enabled=self.storage_health_enabled,
                degraded_mode_enabled=self.storage_degraded_mode_enabled,
                fail_fast_on_critical_missing=self.storage_fail_fast_on_critical_missing,
                require_object_storage_in_production=self.storage_require_object_storage_in_production,
                require_backup_evidence_in_production=self.storage_require_backup_evidence_in_production,
            ),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
