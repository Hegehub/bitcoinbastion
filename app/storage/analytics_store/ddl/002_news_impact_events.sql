-- News impact analytical projection for market reaction windows and source confidence history.
-- narrative_tags and payload_json must be redacted and bounded; canonical article content lives elsewhere.
CREATE TABLE IF NOT EXISTS news_impact_events
(
    event_id String,
    news_article_hash String,
    news_event_hash String,
    source_hash String,
    source_tier LowCardinality(String),
    narrative_tags Array(String),
    occurred_at DateTime64(3, 'UTC'),
    published_at Nullable(DateTime64(3, 'UTC')),
    ingested_at DateTime64(3, 'UTC'),
    asset LowCardinality(String),
    impact_window LowCardinality(String),
    price_move_bps Nullable(Float64),
    volume_change_bps Nullable(Float64),
    volatility_change_bps Nullable(Float64),
    confidence_score Nullable(Float64),
    impact_score Nullable(Float64),
    sentiment_band LowCardinality(String),
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
ORDER BY (asset, occurred_at, impact_window, source_tier);
