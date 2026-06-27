"""Analytics-store abstraction for rebuildable ClickHouse projections."""

from app.storage.analytics_store.base import AnalyticsStore
from app.storage.analytics_store.clickhouse import ClickHouseAnalyticsStore
from app.storage.analytics_store.clickhouse_schema import (
    CLICKHOUSE_ANALYTICS_TABLES,
    CLICKHOUSE_DDL_FILES,
    get_clickhouse_ddl_paths,
    get_clickhouse_table_names,
)
from app.storage.analytics_store.disabled import DisabledAnalyticsStore
from app.storage.analytics_store.errors import (
    AnalyticsStoreConfigurationError,
    AnalyticsStoreDisabledError,
    AnalyticsStoreError,
    AnalyticsStoreInsertError,
    AnalyticsStoreQueryError,
)
from app.storage.analytics_store.health import build_analytics_store, check_analytics_store
from app.storage.analytics_store.schemas import (
    AnalyticsInsertResult,
    AnalyticsQueryResult,
    AnalyticsStoreHealth,
    AnalyticsStoreStatus,
    AnalyticsStoreStatusValue,
)

__all__ = [
    "AnalyticsInsertResult",
    "AnalyticsQueryResult",
    "AnalyticsStore",
    "AnalyticsStoreConfigurationError",
    "AnalyticsStoreDisabledError",
    "AnalyticsStoreError",
    "AnalyticsStoreHealth",
    "AnalyticsStoreInsertError",
    "AnalyticsStoreQueryError",
    "AnalyticsStoreStatus",
    "AnalyticsStoreStatusValue",
    "CLICKHOUSE_ANALYTICS_TABLES",
    "CLICKHOUSE_DDL_FILES",
    "ClickHouseAnalyticsStore",
    "DisabledAnalyticsStore",
    "build_analytics_store",
    "check_analytics_store",
    "get_clickhouse_ddl_paths",
    "get_clickhouse_table_names",
]
