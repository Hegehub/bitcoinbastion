from pathlib import Path

from app.storage.analytics_store.clickhouse_schema import (
    CLICKHOUSE_ANALYTICS_TABLES,
    CLICKHOUSE_DDL_FILES,
    get_clickhouse_ddl_paths,
    get_clickhouse_table_names,
)

EXPECTED_TABLES = {
    "market_time_machine_events",
    "news_impact_events",
    "candle_attribution_events",
    "trace_runtime_events",
    "webhook_delivery_events",
    "operator_replay_events",
    "api_usage_events",
    "analytics_schema_metadata",
}


def test_clickhouse_schema_registry_lists_expected_tables_and_files() -> None:
    assert set(CLICKHOUSE_ANALYTICS_TABLES) == EXPECTED_TABLES
    assert get_clickhouse_table_names() == CLICKHOUSE_ANALYTICS_TABLES
    assert len(CLICKHOUSE_DDL_FILES) == len(EXPECTED_TABLES)
    assert CLICKHOUSE_DDL_FILES[-1] == "999_schema_metadata.sql"


def test_registered_clickhouse_ddl_files_exist() -> None:
    paths = get_clickhouse_ddl_paths()

    assert all(isinstance(path, Path) for path in paths)
    assert all(path.exists() for path in paths)
    assert [path.name for path in paths] == CLICKHOUSE_DDL_FILES


def test_clickhouse_schema_docs_exist() -> None:
    assert Path("app/storage/analytics_store/README.md").exists()
    assert Path("docs/CLICKHOUSE_ANALYTICS_SCHEMA.md").exists()
