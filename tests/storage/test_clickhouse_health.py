import asyncio

from app.core.config import Settings
from app.storage.analytics_store.health import build_analytics_store, check_analytics_store
from app.storage.analytics_store.disabled import DisabledAnalyticsStore


def test_clickhouse_disabled_health_does_not_require_clickhouse() -> None:
    settings = Settings(_env_file=None, CLICKHOUSE_ENABLED=False)
    health = asyncio.run(check_analytics_store(settings))

    assert health.enabled is False
    assert health.status == "disabled"
    assert "secret" not in str(health.model_dump()).lower()


def test_clickhouse_disabled_factory_returns_disabled_store() -> None:
    settings = Settings(_env_file=None, CLICKHOUSE_ENABLED=False)
    assert isinstance(build_analytics_store(settings), DisabledAnalyticsStore)


def test_clickhouse_enabled_missing_dependency_or_connection_is_sanitized() -> None:
    settings = Settings(
        _env_file=None,
        CLICKHOUSE_ENABLED=True,
        CLICKHOUSE_PROFILE="development",
        CLICKHOUSE_PASSWORD="super-secret-password",
    )
    health = asyncio.run(check_analytics_store(settings))
    payload = str(health.model_dump()).lower()

    assert health.enabled is True
    assert health.status in {"unavailable", "misconfigured"}
    assert "super-secret-password" not in payload
    assert "clickhouse://" not in payload
