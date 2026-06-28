from datetime import datetime, UTC

import pytest

from app.db.models.storage_outbox_event import StorageOutboxEvent
from app.storage.projections.clickhouse_projector import (
    SUPPORTED_EVENT_TABLES,
    InvalidProjectionPayloadError,
    UnsupportedEventTypeError,
    map_outbox_event_to_clickhouse_row,
)


def make_event(event_type: str, payload: dict[str, object] | None = None) -> StorageOutboxEvent:
    return StorageOutboxEvent(
        event_id="outbox-1",
        event_type=event_type,
        aggregate_type="market_event",
        aggregate_id="canonical-123",
        payload_json=payload or {"asset": "btc", "occurred_at": "2026-06-26T00:00:00+00:00"},
        metadata_json={"schema_version": 1, "projection_version": 1},
        target_stores=["clickhouse"],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        available_at=datetime.now(UTC),
    )


def test_supported_event_families_map_to_clickhouse_tables() -> None:
    assert set(SUPPORTED_EVENT_TABLES) == {
        "market.time_machine.event",
        "news.impact.event",
        "candle.attribution.event",
        "trace.runtime.event",
        "webhook.delivery.event",
        "api.usage.event",
        "operator.replay.event",
        "provider.health.event",
    }


def test_market_event_maps_to_projection_row_with_common_fields() -> None:
    projected = map_outbox_event_to_clickhouse_row(make_event("market.time_machine.event"))

    assert projected.table == "market_time_machine_events"
    assert len(projected.projection_id) == 64
    assert projected.row["event_id"] == projected.projection_id
    assert projected.row["source_store"] == "storage_outbox"
    assert projected.row["projection_version"] == 1
    assert projected.row["schema_version"] == 1
    assert "canonical-123" not in str(projected.row["source_id_hash"])


def test_unsupported_event_type_raises() -> None:
    with pytest.raises(UnsupportedEventTypeError):
        map_outbox_event_to_clickhouse_row(make_event("unknown.event"))


def test_sensitive_payload_is_rejected() -> None:
    with pytest.raises(InvalidProjectionPayloadError):
        map_outbox_event_to_clickhouse_row(
            make_event("api.usage.event", {"access_token": "raw-token-value"})
        )
