import pytest

from app.storage.constants import CLICKHOUSE, OBJECT_STORAGE, POSTGRES, QDRANT, REDIS
from app.storage.errors import UnsupportedStorageEngineError
from app.storage.registry import build_default_storage_registry


def test_default_registry_includes_postgres_and_redis() -> None:
    registry = build_default_storage_registry()
    assert {POSTGRES, REDIS}.issubset(registry.enabled_engines())
    assert registry.get_engine(POSTGRES).source_of_truth is True


def test_redis_clickhouse_and_qdrant_are_not_source_of_truth() -> None:
    registry = build_default_storage_registry(clickhouse_enabled=True, qdrant_enabled=True)
    assert registry.get_engine(REDIS).source_of_truth is False
    assert registry.get_engine(CLICKHOUSE).source_of_truth is False
    assert registry.get_engine(QDRANT).source_of_truth is False
    assert registry.validate_safety() == []


def test_object_storage_is_described_as_artifact_storage() -> None:
    registry = build_default_storage_registry(object_storage_enabled=True)
    descriptor = registry.get_engine(OBJECT_STORAGE)
    assert descriptor.source_of_truth is True
    assert "artifact bytes" in descriptor.description.lower()
    assert "metadata truth" in descriptor.description.lower()


def test_unknown_engine_raises_clean_error() -> None:
    registry = build_default_storage_registry()
    with pytest.raises(UnsupportedStorageEngineError, match="Unsupported storage engine"):
        registry.get_engine("unknown")
