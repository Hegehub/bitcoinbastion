"""Storage projection workers for rebuildable external stores."""

from app.storage.projections.clickhouse_projector import (
    CLICKHOUSE_TARGET_STORE,
    SUPPORTED_EVENT_TABLES,
    ClickHouseOutboxProjector,
    ClickHouseProjectionError,
    InvalidProjectionPayloadError,
    ProjectionMappingError,
    UnsupportedEventTypeError,
    build_projection_id,
    map_outbox_event_to_clickhouse_row,
)
from app.storage.projections.schemas import ClickHouseProjectionSummary

__all__ = [
    "CLICKHOUSE_TARGET_STORE",
    "SUPPORTED_EVENT_TABLES",
    "ClickHouseOutboxProjector",
    "ClickHouseProjectionError",
    "ClickHouseProjectionSummary",
    "InvalidProjectionPayloadError",
    "ProjectionMappingError",
    "UnsupportedEventTypeError",
    "build_projection_id",
    "map_outbox_event_to_clickhouse_row",
]
