from datetime import UTC, datetime

import pytest

from app.services.access.offline_validity_pack import (
    OfflinePackError,
    append_local_event,
    verify_local_event_chain,
)


def test_local_queue_chain_detects_tampering_before_reconciliation():
    events = []
    append_local_event(
        events, "local_pack_imported", {"pack_fingerprint": "sha256:pack"}, datetime.now(UTC)
    )
    append_local_event(
        events,
        "local_offline_operation_allowed",
        {"operation": "cached_metric_read"},
        datetime.now(UTC),
    )
    assert verify_local_event_chain(events) == events[-1]["event_hash"]
    events[0]["safe_details"]["pack_fingerprint"] = "sha256:tampered"
    with pytest.raises(OfflinePackError, match="event_chain_invalid"):
        verify_local_event_chain(events)
