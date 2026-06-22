from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.storage.health_checks import collect_storage_status_sync
from app.storage.schemas import StorageStatusValue
from app.storage.timeseries.health import check_timescale


class _FakeRedis:
    def ping(self) -> bool:
        return True


def test_timescale_health_reports_disabled_when_feature_flag_is_false() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    settings = Settings(_env_file=None, TIMESCALE_ENABLED=False)

    with Session(engine) as session:
        status = check_timescale(settings, session)

    assert status.status == StorageStatusValue.DISABLED
    assert status.details["enabled"] is False
    assert status.details["schema"] == "public"
    assert "TIMESCALE_ENABLED=false" in status.details["reason"]


def test_timescale_enabled_with_sqlite_reports_degraded_without_secret_leak() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    settings = Settings(
        _env_file=None,
        TIMESCALE_ENABLED=True,
        TIMESCALE_URL="postgresql://user:super-secret@example.internal/db",
    )

    with Session(engine) as session:
        status = check_timescale(settings, session)

    payload = status.model_dump()
    assert status.status == StorageStatusValue.DEGRADED
    assert payload["details"]["enabled"] is True
    assert payload["details"]["extension_available"] is False
    assert "super-secret" not in repr(payload)
    assert "postgresql://" not in repr(payload)


def test_storage_status_response_includes_timescale_state_when_enabled() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    settings = Settings(_env_file=None, TIMESCALE_ENABLED=True)

    with Session(engine) as session:
        response = collect_storage_status_sync(
            settings=settings,
            db=session,
            redis_client_factory=_FakeRedis,
        )

    timescale = response.stores["timescale"]
    assert timescale.status == StorageStatusValue.DEGRADED
    assert timescale.details["enabled"] is True
    assert timescale.details["schema"] == "public"
