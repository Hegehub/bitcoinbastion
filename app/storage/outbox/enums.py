from enum import StrEnum


class StorageOutboxEventStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    RETRY = "retry"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"
    CANCELLED = "cancelled"


class StorageOutboxTargetStore(StrEnum):
    TIMESCALE = "timescale"
    CLICKHOUSE = "clickhouse"
    QDRANT = "qdrant"
    PGVECTOR = "pgvector"
    OBJECT_STORAGE = "object_storage"
    REDIS = "redis"
    WEBHOOK = "webhook"
    WEBSOCKET = "websocket"
    SDK = "sdk"
    MCP = "mcp"
    AUDIT = "audit"
