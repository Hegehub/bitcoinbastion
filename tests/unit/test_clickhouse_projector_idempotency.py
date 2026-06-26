from tests.unit.test_clickhouse_projector_mapping import make_event

from app.storage.projections.clickhouse_projector import (
    build_projection_id,
    map_outbox_event_to_clickhouse_row,
)


def test_projection_id_is_deterministic_for_same_outbox_event() -> None:
    event = make_event("api.usage.event")

    assert build_projection_id(event) == build_projection_id(event)
    assert map_outbox_event_to_clickhouse_row(event).projection_id == build_projection_id(event)


def test_projection_id_changes_when_outbox_event_changes() -> None:
    first = make_event("api.usage.event")
    second = make_event("api.usage.event")
    second.event_id = "outbox-2"

    assert build_projection_id(first) != build_projection_id(second)
