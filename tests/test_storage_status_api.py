from pathlib import Path

from fastapi.testclient import TestClient
from redis import RedisError
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1 import storage_status as storage_status_module
from app.core.config import Settings
from app.main import app


class FakeDB:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    def execute(self, statement: object) -> None:
        if self.fail:
            raise SQLAlchemyError("postgres://user:password@private-host/db failed")


class FakeRedis:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    def ping(self) -> bool:
        if self.fail:
            raise RedisError("redis://:secret@private-redis:6379/0 failed")
        return True


def _override_db(fake_db: FakeDB):
    def _dependency():
        yield fake_db

    app.dependency_overrides[storage_status_module.db_session] = _dependency


def _settings(**overrides: object) -> Settings:
    values = {
        "DATABASE_URL": "sqlite+pysqlite:///:memory:",
        "REDIS_URL": "redis://localhost:6379/0",
        "STORAGE_PROFILE": "development",
        "OBJECT_STORAGE_ENABLED": False,
        "OBJECT_STORAGE_BACKEND": "disabled",
        "OBJECT_STORAGE_PROVIDER": "disabled",
    }
    values.update(overrides)
    return Settings(**values)


def _client(
    monkeypatch,
    *,
    settings: Settings | None = None,
    db_fail: bool = False,
    redis_fail: bool = False,
):
    app.dependency_overrides.clear()
    _override_db(FakeDB(fail=db_fail))
    monkeypatch.setattr(storage_status_module, "get_settings", lambda: settings or _settings())
    monkeypatch.setattr(
        storage_status_module,
        "get_redis_client",
        lambda: FakeRedis(fail=redis_fail),
    )
    return TestClient(app)


def test_storage_status_endpoint_returns_200_when_optional_stores_disabled(monkeypatch) -> None:
    client = _client(monkeypatch)

    response = client.get("/api/v1/storage/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ok", "degraded"}
    assert payload["summary"]["required_ok"] is True


def test_storage_status_response_includes_all_expected_store_keys(monkeypatch) -> None:
    client = _client(monkeypatch)

    payload = client.get("/api/v1/storage/status").json()

    assert list(payload["stores"].keys()) == [
        "postgres",
        "redis",
        "object_storage",
        "timescale",
        "clickhouse",
        "qdrant",
        "sqlite_local",
        "duckdb_local",
    ]


def test_required_postgres_failure_changes_overall_status_to_unavailable(monkeypatch) -> None:
    client = _client(monkeypatch, db_fail=True)

    payload = client.get("/api/v1/storage/status").json()

    assert payload["status"] == "unavailable"
    assert payload["stores"]["postgres"]["status"] == "unavailable"
    assert payload["summary"]["critical_failures"] == 1


def test_disabled_future_stores_do_not_crash_endpoint(monkeypatch) -> None:
    client = _client(monkeypatch)

    stores = client.get("/api/v1/storage/status").json()["stores"]

    assert stores["timescale"]["status"] == "disabled"
    assert stores["clickhouse"]["status"] == "disabled"
    assert stores["qdrant"]["status"] == "disabled"


def test_storage_status_response_never_leaks_secret_exception_messages(monkeypatch) -> None:
    client = _client(monkeypatch, db_fail=True, redis_fail=True)

    response_text = client.get("/api/v1/storage/status").text

    assert "password" not in response_text
    assert "secret" not in response_text
    assert "private-host" not in response_text
    assert "private-redis" not in response_text
    assert "OperationalError" not in response_text
    assert "SQLAlchemyError" in response_text
    assert "RedisError" in response_text


def test_object_storage_disabled_is_reported_honestly(monkeypatch) -> None:
    client = _client(monkeypatch)

    object_storage = client.get("/api/v1/storage/status").json()["stores"]["object_storage"]

    assert object_storage["status"] == "disabled"
    assert object_storage["details"]["reason"] == "OBJECT_STORAGE_ENABLED=false"


def test_local_object_storage_health_reports_ok(monkeypatch, tmp_path: Path) -> None:
    settings = _settings(
        OBJECT_STORAGE_ENABLED=True,
        OBJECT_STORAGE_BACKEND="local",
        OBJECT_STORAGE_PROVIDER="local",
        OBJECT_STORAGE_BUCKET="bastion-health",
        OBJECT_STORAGE_LOCAL_ROOT=str(tmp_path),
    )
    client = _client(monkeypatch, settings=settings)

    object_storage = client.get("/api/v1/storage/status").json()["stores"]["object_storage"]

    assert object_storage["status"] == "ok"
    assert object_storage["details"]["backend"] == "local"
    assert object_storage["details"]["write_check"] == "ok"


def test_redis_unavailable_is_reported_without_hiding_failure(monkeypatch) -> None:
    client = _client(monkeypatch, redis_fail=True)

    payload = client.get("/api/v1/storage/status").json()

    assert payload["status"] == "unavailable"
    assert payload["stores"]["redis"]["status"] == "unavailable"
    assert payload["stores"]["redis"]["details"] == {
        "connection": "failed",
        "error_class": "RedisError",
    }


def test_storage_status_openapi_schema_is_present(monkeypatch) -> None:
    client = _client(monkeypatch)

    schema = client.get("/openapi.json").json()

    operation = schema["paths"]["/api/v1/storage/status"]["get"]
    assert operation["summary"] == "Storage status for Bitcoin Bastion storage engines."
    assert "StorageStatusResponse" in str(operation)
