-- Webhook delivery analytics. webhook_endpoint_hash is a fingerprint only.
-- Do not store endpoint URLs, signing material, headers, or delivery payload bodies.
CREATE TABLE IF NOT EXISTS webhook_delivery_events
(
    event_id String,
    webhook_endpoint_hash String,
    workspace_id_hash String,
    event_type LowCardinality(String),
    delivery_status LowCardinality(String),
    attempt_number UInt16,
    http_status Nullable(UInt16),
    error_class LowCardinality(String),
    latency_ms Nullable(UInt32),
    occurred_at DateTime64(3, 'UTC'),
    ingested_at DateTime64(3, 'UTC'),
    source_store LowCardinality(String),
    source_table LowCardinality(String),
    source_id_hash String,
    payload_size_bytes Nullable(UInt64),
    payload_json String,
    projection_version UInt32,
    schema_version UInt32,
    created_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(occurred_at)
ORDER BY (webhook_endpoint_hash, event_type, occurred_at, delivery_status);
