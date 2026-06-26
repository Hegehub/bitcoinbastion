from app.storage.analytics_store.clickhouse_schema import get_clickhouse_ddl_paths

FORBIDDEN_RAW_COLUMNS = {
    "seed_phrase",
    "private_key",
    "wallet_file",
    "xprv",
    "yprv",
    "zprv",
    "raw_email",
    "raw_ip",
    "raw_telegram_id",
    "webhook_secret",
    "access_pass_token",
    "api_key_plaintext",
}

EVENT_TABLE_COMMON_COLUMNS = {
    "event_id",
    "occurred_at",
    "ingested_at",
    "source_store",
    "source_table",
    "source_id_hash",
    "projection_version",
    "schema_version",
    "created_at",
}


def _ddl_by_name() -> dict[str, str]:
    return {path.name: path.read_text(encoding="utf-8") for path in get_clickhouse_ddl_paths()}


def test_clickhouse_ddl_uses_safe_create_table_shape() -> None:
    for ddl in _ddl_by_name().values():
        normalized = ddl.lower()
        assert "create table if not exists" in normalized
        assert "engine = mergetree" in normalized
        assert "datetime64(3, 'utc')" in normalized
        assert "order by" in normalized


def test_clickhouse_event_tables_include_projection_columns() -> None:
    ddl_files = _ddl_by_name()
    for filename, ddl in ddl_files.items():
        if filename == "999_schema_metadata.sql":
            continue
        normalized = ddl.lower()
        for column in EVENT_TABLE_COMMON_COLUMNS:
            assert column in normalized, f"{filename} missing {column}"


def test_clickhouse_ddl_avoids_forbidden_raw_sensitive_columns() -> None:
    combined = "\n".join(_ddl_by_name().values()).lower()

    for forbidden in FORBIDDEN_RAW_COLUMNS:
        assert forbidden not in combined


def test_clickhouse_ddl_uses_partitioning_for_large_event_tables() -> None:
    ddl_files = _ddl_by_name()
    for filename, ddl in ddl_files.items():
        if filename == "999_schema_metadata.sql":
            continue
        assert "partition by toyyyymm(" in ddl.lower()


def test_clickhouse_metadata_table_tracks_schema_version_and_hash() -> None:
    metadata = _ddl_by_name()["999_schema_metadata.sql"].lower()

    assert "analytics_schema_metadata" in metadata
    assert "schema_version" in metadata
    assert "ddl_hash" in metadata
    assert "order by (schema_name, schema_version)" in metadata
