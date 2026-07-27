from datetime import UTC, datetime, timedelta

from app.services.access.offline_policy import OfflinePolicyEvaluator


def test_privileged_operation_denied_without_trusted_time():
    now = datetime.now(UTC)
    pack = {
        "principal": {"principal_hash": "hmac-sha256:p"},
        "device_binding": {"device_key_fingerprint": "sha256:d"},
        "offline_policy": {
            "profile": "payregister_cashier_shift",
            "allowed_actions": ["payregister_invoice_create"],
            "quota": {"maximum_operations": 1},
        },
        "validity": {
            "issued_at": now.isoformat(),
            "not_before": now.isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
            "maximum_offline_seconds": 3600,
        },
        "reconciliation": {"maximum_pending_events": 1},
    }
    decision = OfflinePolicyEvaluator().evaluate(
        pack,
        operation="payregister_invoice_create",
        device_key_fingerprint="sha256:d",
        principal_hash="hmac-sha256:p",
        now=now,
        trusted_time_available=False,
    )
    assert decision.reason_code == "trusted_time_unavailable"
