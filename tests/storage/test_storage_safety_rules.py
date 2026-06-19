from app.storage.constants import CLICKHOUSE, DUCKDB, QDRANT, REDIS
from app.storage.interfaces import StorageEngineDescriptor
from app.storage.registry import StorageRegistry, build_default_storage_registry


def test_forbidden_sensitive_material_is_not_allowed_in_descriptors() -> None:
    registry = StorageRegistry(
        [
            StorageEngineDescriptor(
                name="unsafe",
                role="test",
                enabled=True,
                source_of_truth=False,
                stores_sensitive_material=True,
                description="Unsafe descriptor for test only.",
            )
        ]
    )
    warnings = registry.validate_safety()
    assert any("forbidden sensitive material" in warning for warning in warnings)
    assert any("seed_phrase" in warning for warning in warnings)


def test_registry_safety_flags_invalid_source_of_truth_engines() -> None:
    registry = StorageRegistry(
        [
            StorageEngineDescriptor(REDIS, "ephemeral_state", True, True, False, "bad"),
            StorageEngineDescriptor(CLICKHOUSE, "analytics", True, True, False, "bad"),
            StorageEngineDescriptor(QDRANT, "semantic_memory", True, True, False, "bad"),
            StorageEngineDescriptor(DUCKDB, "local_analytics", True, True, False, "bad"),
        ]
    )
    warnings = registry.validate_safety()
    assert "redis must not be marked as source_of_truth" in warnings
    assert "clickhouse must not be source_of_truth for transactional access decisions" in warnings
    assert "qdrant must not be marked as canonical source_of_truth" in warnings
    assert "duckdb must not be operational truth" in warnings


def test_default_registry_does_not_store_forbidden_sensitive_material() -> None:
    registry = build_default_storage_registry(
        object_storage_enabled=True,
        timescale_enabled=True,
        clickhouse_enabled=True,
        qdrant_enabled=True,
        sqlite_enabled=True,
        duckdb_enabled=True,
    )
    assert all(not descriptor.stores_sensitive_material for descriptor in registry.list_engines())
    assert registry.validate_safety() == []
