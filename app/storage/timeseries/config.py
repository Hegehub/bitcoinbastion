"""TimescaleDB configuration helpers for the storage foundation."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings


@dataclass(frozen=True)
class TimescaleConfig:
    """Runtime TimescaleDB settings used by health and migration helpers."""

    enabled: bool = False
    create_extension: bool = False
    schema: str = "public"
    default_chunk_interval: str = "1 day"
    health_timeout_seconds: int = 2
    url_configured: bool = False

    @classmethod
    def from_settings(cls, settings: Settings) -> "TimescaleConfig":
        return cls(
            enabled=settings.timescale_enabled,
            create_extension=settings.timescale_create_extension,
            schema=settings.timescale_schema,
            default_chunk_interval=settings.timescale_default_chunk_interval,
            health_timeout_seconds=settings.timescale_health_timeout_seconds,
            url_configured=bool(settings.timescale_url.strip()),
        )
