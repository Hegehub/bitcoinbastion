-- API usage analytics for SDK, MCP, CLI, quota, and developer trends.
-- payload_json must not include request bodies, response bodies, bearer values, or raw credentials.
CREATE TABLE IF NOT EXISTS api_usage_events
(
    event_id String,
    occurred_at DateTime64(3, 'UTC'),
    ingested_at DateTime64(3, 'UTC'),
    client_type LowCardinality(String),
    api_surface LowCardinality(String),
    endpoint_family LowCardinality(String),
    method LowCardinality(String),
    status_family LowCardinality(String),
    plan_code LowCardinality(String),
    workspace_id_hash String,
    pass_lookup_hash String,
    api_key_hash String,
    session_id_hash String,
    latency_ms Nullable(UInt32),
    request_size_bytes Nullable(UInt64),
    response_size_bytes Nullable(UInt64),
    metric_cost Nullable(UInt32),
    rate_limited UInt8,
    policy_decision LowCardinality(String),
    source_store LowCardinality(String),
    source_table LowCardinality(String),
    source_id_hash String,
    payload_json String,
    projection_version UInt32,
    schema_version UInt32,
    created_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(occurred_at)
ORDER BY (api_surface, endpoint_family, occurred_at, plan_code);
