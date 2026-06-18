from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Environment settings for the parallel Reflex frontend API layer."""

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
    log_level: LogLevel = "INFO"

    @field_validator("api_base_url")
    @classmethod
    def strip_api_base_url(cls, value: str) -> str:
        normalized = value.strip().rstrip("/")
        if not normalized:
            msg = "BB_API_BASE_URL must not be empty."
            raise ValueError(msg)
        return normalized

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: object) -> object:
        if isinstance(value, str):
            return value.upper()
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
