-- Operator replay analytics. This is not the canonical audit chain.
-- payload_json must reference redacted evidence or hashes, not sensitive operational payloads.
CREATE TABLE IF NOT EXISTS operator_replay_events
(
    event_id String,
    operator_event_type LowCardinality(String),
    occurred_at DateTime64(3, 'UTC'),
    ingested_at DateTime64(3, 'UTC'),
    actor_hash String,
    workspace_id_hash String,
    object_hash String,
    object_type LowCardinality(String),
    decision LowCardinality(String),
    risk_band LowCardinality(String),
    policy_version_hash String,
    audit_event_hash String,
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
ORDER BY (workspace_id_hash, occurred_at, operator_event_type);
