"""Canonical names and safety labels for the storage abstraction layer."""

POSTGRES = "postgres"
TIMESCALE = "timescale"
CLICKHOUSE = "clickhouse"
QDRANT = "qdrant"
PGVECTOR = "pgvector"
REDIS = "redis"
OBJECT_STORAGE = "object_storage"
SQLITE = "sqlite"
DUCKDB = "duckdb"

TRANSACTIONAL_TRUTH = "transactional_truth"
TIME_SERIES = "time_series"
ANALYTICS = "analytics"
SEMANTIC_MEMORY = "semantic_memory"
EPHEMERAL_STATE = "ephemeral_state"
ARTIFACT_STORAGE = "artifact_storage"
LOCAL_OPERATIONAL = "local_operational"
LOCAL_ANALYTICS = "local_analytics"

STORAGE_ENGINE_RESPONSIBILITIES = {
    POSTGRES: [TRANSACTIONAL_TRUTH],
    TIMESCALE: [TIME_SERIES],
    CLICKHOUSE: [ANALYTICS],
    QDRANT: [SEMANTIC_MEMORY],
    PGVECTOR: [SEMANTIC_MEMORY],
    REDIS: [EPHEMERAL_STATE],
    OBJECT_STORAGE: [ARTIFACT_STORAGE],
    SQLITE: [LOCAL_OPERATIONAL],
    DUCKDB: [LOCAL_ANALYTICS],
}

FORBIDDEN_STORAGE_MATERIAL = [
    "seed_phrase",
    "bitcoin_private_key",
    "wallet_file",
    "xprv",
    "yprv",
    "zprv",
    "mnemonic",
    "raw_secret",
]
