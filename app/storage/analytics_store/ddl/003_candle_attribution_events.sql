-- Candle attribution analytical projection for explanations and candidate ranking history.
-- payload_json must contain safe diagnostics only; canonical candles and evidence remain outside ClickHouse.
CREATE TABLE IF NOT EXISTS candle_attribution_events
(
    event_id String,
    candle_hash String,
    asset LowCardinality(String),
    timeframe LowCardinality(String),
    candle_open_time DateTime64(3, 'UTC'),
    candidate_type LowCardinality(String),
    candidate_hash String,
    candidate_rank UInt16,
    attribution_score Nullable(Float64),
    confidence_score Nullable(Float64),
    explanation_hash String,
    limitations Array(String),
    occurred_at DateTime64(3, 'UTC'),
    ingested_at DateTime64(3, 'UTC'),
    source_store LowCardinality(String),
    source_table LowCardinality(String),
    source_id_hash String,
    payload_json String,
    projection_version UInt32,
    schema_version UInt32,
    created_at DateTime64(3, 'UTC')
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(candle_open_time)
ORDER BY (asset, timeframe, candle_open_time, candidate_rank);
