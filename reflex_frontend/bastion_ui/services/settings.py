from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment settings for the parallel Reflex migration shell."""

    model_config = SettingsConfigDict(env_prefix="BB_", env_file=".env", extra="ignore")

    api_base_url: str = "http://localhost:8000"
    public_site_mode: bool = True
    enable_trace: bool = True
    enable_market: bool = True
    enable_time_machine: bool = True
    enable_sovereign_grid: bool = True
    enable_console: bool = True
    request_timeout_seconds: float = Field(default=5.0, gt=0)
    default_language: str = "en"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
