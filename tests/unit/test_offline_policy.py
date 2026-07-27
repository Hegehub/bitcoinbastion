from datetime import UTC, datetime, timedelta

from app.services.access.offline_policy import OfflinePolicyEvaluator


def pack(now):
    return {
        "principal": {"principal_hash": "hmac-sha256:p"},
        "device_binding": {"device_key_fingerprint": "sha256:d"},
        "offline_policy": {
            "profile": "read_only",
            "allowed_actions": ["cached_metric_read"],
            "quota": {"maximum_operations": 2},
            "maximum_value_limits": {},
        },
        "validity": {
            "issued_at": now.isoformat(),
            "not_before": now.isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
            "maximum_offline_seconds": 3600,
        },
        "reconciliation": {"maximum_pending_events": 2},
    }


def test_unknown_and_treasury_actions_default_deny():
    now = datetime.now(UTC)
    evaluator = OfflinePolicyEvaluator()
    value = pack(now)
    assert not evaluator.evaluate(
        value,
        operation="unknown",
        device_key_fingerprint="sha256:d",
        principal_hash="hmac-sha256:p",
        now=now,
    ).allowed
    assert not evaluator.evaluate(
        value,
        operation="transaction_sign",
        device_key_fingerprint="sha256:d",
        principal_hash="hmac-sha256:p",
        now=now,
    ).allowed
    assert evaluator.evaluate(
        value,
        operation="cached_metric_read",
        device_key_fingerprint="sha256:d",
        principal_hash="hmac-sha256:p",
        now=now,
    ).allowed


def test_clock_rollback_quota_and_queue_are_denied():
    now = datetime.now(UTC)
    evaluator = OfflinePolicyEvaluator()
    value = pack(now)
    assert (
        evaluator.evaluate(
            value,
            operation="cached_metric_read",
            device_key_fingerprint="sha256:d",
            principal_hash="hmac-sha256:p",
            now=now,
            last_trusted_at=now + timedelta(seconds=1),
        ).reason_code
        == "clock_rollback_detected"
    )
    assert (
        evaluator.evaluate(
            value,
            operation="cached_metric_read",
            device_key_fingerprint="sha256:d",
            principal_hash="hmac-sha256:p",
            now=now,
            local_operation_count=2,
        ).reason_code
        == "quota_exceeded"
    )
    assert (
        evaluator.evaluate(
            value,
            operation="cached_metric_read",
            device_key_fingerprint="sha256:d",
            principal_hash="hmac-sha256:p",
            now=now,
            queued_event_count=2,
        ).reason_code
        == "reconciliation_required"
    )
