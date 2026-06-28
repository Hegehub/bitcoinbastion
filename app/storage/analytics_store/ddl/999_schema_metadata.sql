-- ClickHouse analytics schema metadata. Tracks applied schema definitions only.
CREATE TABLE IF NOT EXISTS analytics_schema_metadata
(
    schema_name String,
    schema_version UInt32,
    ddl_hash String,
    applied_at DateTime64(3, 'UTC'),
    description String
)
ENGINE = MergeTree
ORDER BY (schema_name, schema_version);
