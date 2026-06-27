-- Privacy-safe Trace runtime analytics. address_hash and report_hash are fingerprints only.
-- Do not project raw blockchain addresses, report IDs, provider credentials, or sensitive payloads.
CREATE TABLE IF NOT EXISTS trace_runtime_events
(
    event_id String,
    trace_event_type LowCardinality(String),
    occurred_at DateTime64(3, 'UTC'),
    ingested_at DateTime64(3, 'UTC'),
    report_hash String,
    address_hash String,
    workspace_id_hash String,
    risk_band LowCardinality(String),
    confidence_band LowCardinality(String),
    provider_count UInt16,
    disagreement_band LowCardinality(String),
    privacy_exposure_band LowCardinality(String),
    review_status LowCardinality(String),
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
ORDER BY (trace_event_type, occurred_at, risk_band, confidence_band);
