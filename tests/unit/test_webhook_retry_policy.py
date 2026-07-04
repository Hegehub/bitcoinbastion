from datetime import datetime, timezone

from app.services.events.webhook_dispatcher import (
    calculate_retry_delay_seconds,
    next_retry_at_for_attempt,
)


def test_retry_policy_uses_bounded_exponential_backoff() -> None:
    assert calculate_retry_delay_seconds(1) == 30
    assert calculate_retry_delay_seconds(2) == 60
    assert calculate_retry_delay_seconds(3) == 120
    assert calculate_retry_delay_seconds(99) == 3600


def test_next_retry_at_is_deterministic_for_fixed_time() -> None:
    now = datetime(2026, 6, 8, 12, 0, tzinfo=timezone.utc)

    assert next_retry_at_for_attempt(2, now=now).isoformat() == "2026-06-08T12:01:00+00:00"
