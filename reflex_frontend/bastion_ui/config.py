from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """Runtime configuration for the parallel Reflex frontend.

    The backend is not contacted while loading configuration.
    """

    model_config = SettingsConfigDict(env_prefix="BB_", env_file=".env", extra="ignore")

    api_base_url: str = "http://localhost:8000"
    request_timeout_seconds: float = Field(default=5.0, gt=0)
    public_site_mode: bool = True
    enable_trace: bool = True
    enable_market: bool = True
    enable_time_machine: bool = True
    enable_console: bool = True
    enable_sovereign_grid: bool = True
    default_language: str = "en"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    access_dev_signer_enabled: bool = False
    access_payment_poll_interval_ms: int = Field(default=5000, gt=0)
    access_session_refresh_seconds: int = Field(default=300, gt=0)

    @field_validator("api_base_url")
    @classmethod
    def strip_api_base_url(cls, value: str) -> str:
        normalized = value.strip().rstrip("/")
        if not normalized:
            raise ValueError("BB_API_BASE_URL must not be empty")
        return normalized


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    return AppConfig()
