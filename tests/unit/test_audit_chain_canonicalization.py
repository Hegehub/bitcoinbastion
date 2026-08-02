from datetime import UTC, datetime

from app.services.access.audit_chain import build_canonical_event, compute_event_hash


def test_order_timestamp_and_version_are_deterministic_and_sensitive() -> None:
    at = datetime(2026, 7, 26, 12, tzinfo=UTC)
    first = build_canonical_event(
        event_type="wallet_login_success",
        metadata={"action": "login", "reason_code": "verified"},
        occurred_at=at,
    )
    reordered = build_canonical_event(
        event_type="wallet_login_success",
        metadata={"reason_code": "verified", "action": "login"},
        occurred_at=at,
    )
    changed = build_canonical_event(
        event_type="wallet_login_success",
        metadata={"action": "login", "reason_code": "verified"},
        occurred_at=at,
        event_version=2,
    )
    assert first["occurred_at"] == "2026-07-26T12:00:00Z"
    assert compute_event_hash(None, first) == compute_event_hash(None, reordered)
    assert compute_event_hash(None, first) != compute_event_hash(None, changed)
