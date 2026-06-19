"""Registry of configured storage engines and safety invariants."""

from collections.abc import Iterable

from app.storage.constants import (
    ANALYTICS,
    ARTIFACT_STORAGE,
    CLICKHOUSE,
    DUCKDB,
    EPHEMERAL_STATE,
    FORBIDDEN_STORAGE_MATERIAL,
    LOCAL_ANALYTICS,
    LOCAL_OPERATIONAL,
    OBJECT_STORAGE,
    PGVECTOR,
    POSTGRES,
    QDRANT,
    REDIS,
    SEMANTIC_MEMORY,
    SQLITE,
    TIME_SERIES,
    TIMESCALE,
    TRANSACTIONAL_TRUTH,
)
from app.storage.errors import UnsupportedStorageEngineError
from app.storage.interfaces import StorageEngineDescriptor


class StorageRegistry:
    def __init__(self, descriptors: Iterable[StorageEngineDescriptor]) -> None:
        self._descriptors = {descriptor.name: descriptor for descriptor in descriptors}

    def list_engines(self) -> list[StorageEngineDescriptor]:
        return list(self._descriptors.values())

    def get_engine(self, name: str) -> StorageEngineDescriptor:
        try:
            return self._descriptors[name]
        except KeyError as exc:
            raise UnsupportedStorageEngineError(f"Unsupported storage engine: {name}") from exc

    def enabled_engines(self) -> set[str]:
        return {descriptor.name for descriptor in self._descriptors.values() if descriptor.enabled}

    def source_of_truth_engines(self) -> list[StorageEngineDescriptor]:
        return [
            descriptor for descriptor in self._descriptors.values() if descriptor.source_of_truth
        ]

    def validate_safety(self) -> list[str]:
        warnings: list[str] = []

        for descriptor in self._descriptors.values():
            if descriptor.stores_sensitive_material:
                warnings.append(
                    f"{descriptor.name} is marked as storing forbidden sensitive material; "
                    f"forbidden labels include {', '.join(FORBIDDEN_STORAGE_MATERIAL)}"
                )

        redis = self._descriptors.get(REDIS)
        if redis and redis.source_of_truth:
            warnings.append("redis must not be marked as source_of_truth")

        clickhouse = self._descriptors.get(CLICKHOUSE)
        if clickhouse and clickhouse.source_of_truth:
            warnings.append(
                "clickhouse must not be source_of_truth for transactional access decisions"
            )

        for vector_engine in (QDRANT, PGVECTOR):
            descriptor = self._descriptors.get(vector_engine)
            if descriptor and descriptor.source_of_truth:
                warnings.append(f"{vector_engine} must not be marked as canonical source_of_truth")

        object_storage = self._descriptors.get(OBJECT_STORAGE)
        if object_storage and object_storage.source_of_truth:
            if "artifact bytes" not in object_storage.description.lower():
                warnings.append(
                    "object_storage may be source_of_truth only for artifact bytes; "
                    "artifact metadata truth must remain in postgres"
                )

        sqlite = self._descriptors.get(SQLITE)
        if sqlite and sqlite.source_of_truth:
            warnings.append("sqlite may be local offline truth only until sync, not global truth")

        duckdb = self._descriptors.get(DUCKDB)
        if duckdb and duckdb.source_of_truth:
            warnings.append("duckdb must not be operational truth")

        return warnings


def build_default_storage_registry(
    *,
    postgres_enabled: bool = True,
    redis_enabled: bool = True,
    object_storage_enabled: bool = False,
    timescale_enabled: bool = False,
    clickhouse_enabled: bool = False,
    qdrant_enabled: bool = False,
    pgvector_enabled: bool = False,
    sqlite_enabled: bool = False,
    duckdb_enabled: bool = False,
) -> StorageRegistry:
    descriptors = [
        StorageEngineDescriptor(
            name=POSTGRES,
            role=TRANSACTIONAL_TRUTH,
            enabled=postgres_enabled,
            source_of_truth=True,
            stores_sensitive_material=False,
            description="Transactional source of truth for critical relational state and artifact metadata.",
        ),
        StorageEngineDescriptor(
            name=TIMESCALE,
            role=TIME_SERIES,
            enabled=timescale_enabled,
            source_of_truth=True,
            stores_sensitive_material=False,
            description="Canonical time-series store for metrics, candles, and provider/source health history.",
        ),
        StorageEngineDescriptor(
            name=CLICKHOUSE,
            role=ANALYTICS,
            enabled=clickhouse_enabled,
            source_of_truth=False,
            stores_sensitive_material=False,
            description="Analytics warehouse and projection target; never transactional access truth.",
        ),
        StorageEngineDescriptor(
            name=QDRANT,
            role=SEMANTIC_MEMORY,
            enabled=qdrant_enabled,
            source_of_truth=False,
            stores_sensitive_material=False,
            description="Semantic memory projection for similarity search; canonical documents live elsewhere.",
        ),
        StorageEngineDescriptor(
            name=PGVECTOR,
            role=SEMANTIC_MEMORY,
            enabled=pgvector_enabled,
            source_of_truth=False,
            stores_sensitive_material=False,
            description="Postgres-hosted semantic projection for similarity search; not canonical truth.",
        ),
        StorageEngineDescriptor(
            name=REDIS,
            role=EPHEMERAL_STATE,
            enabled=redis_enabled,
            source_of_truth=False,
            stores_sensitive_material=False,
            description="Cache, queue, rate-limit, websocket fanout, and short-lived state only; not durable truth.",
        ),
        StorageEngineDescriptor(
            name=OBJECT_STORAGE,
            role=ARTIFACT_STORAGE,
            enabled=object_storage_enabled,
            source_of_truth=True,
            stores_sensitive_material=False,
            description=(
                "Artifact storage for proof packet and evidence archive artifact bytes; "
                "postgres remains metadata truth."
            ),
        ),
        StorageEngineDescriptor(
            name=SQLITE,
            role=LOCAL_OPERATIONAL,
            enabled=sqlite_enabled,
            source_of_truth=False,
            stores_sensitive_material=False,
            description="Local/offline operational store until sync; not global system truth.",
        ),
        StorageEngineDescriptor(
            name=DUCKDB,
            role=LOCAL_ANALYTICS,
            enabled=duckdb_enabled,
            source_of_truth=False,
            stores_sensitive_material=False,
            description="Local analytics and report store; rebuildable and not operational truth.",
        ),
    ]
    return StorageRegistry(descriptors)
