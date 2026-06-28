-- Market Time Machine analytical projection for long-range replay.
-- payload_json must contain only redacted metadata; never secrets or raw private identifiers.
CREATE TABLE IF NOT EXISTS market_time_machine_events
(
    event_id String,
    event_type LowCardinality(String),
    occurred_at DateTime64(3, 'UTC'),
    ingested_at DateTime64(3, 'UTC'),
    asset LowCardinality(String),
    market_venue LowCardinality(String),
    timeframe LowCardinality(String),
    regime LowCardinality(String),
    confidence_band LowCardinality(String),
    signal_family LowCardinality(String),
    source_store LowCardinality(String),
    source_table LowCardinality(String),
    source_id_hash String,
    correlation_id_hash String,
    payload_json String,
    projection_version UInt32,
    schema_version UInt32,
    created_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(occurred_at)
ORDER BY (asset, timeframe, occurred_at, event_type);
