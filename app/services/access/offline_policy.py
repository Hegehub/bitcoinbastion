"""Restrictive local policy for signed Offline Validity Packs.

This is not the online Policy Engine. It can only narrow its signed snapshot and
defaults to deny when evidence or an operation definition is missing.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any


class OfflineProfile(StrEnum):
    READ_ONLY = "read_only"
    ANALYST_CACHED = "analyst_cached"
    PAYREGISTER_CASHIER_SHIFT = "payregister_cashier_shift"
    BUSINESS_DEGRADED = "business_degraded"


FORBIDDEN_OFFLINE_ACTIONS = frozenset(
    {
        "treasury_policy_change",
        "transaction_sign",
        "transaction_broadcast",
        "api_key_create",
        "enterprise_policy_change",
        "business_owner_replace",
        "recovery_complete",
        "lockdown_release",
        "administrator_enroll",
        "high_privilege_device_enroll",
        "entitlement_upgrade",
        "entitlement_renew",
        "high_value_refund_approve",
        "lnurl_withdraw_execute",
        "payregister_admin",
        "role_assign",
        "payout_execute",
        "fresh_network_retrieval",
    }
)

PROFILE_RULES: dict[OfflineProfile, dict[str, Any]] = {
    OfflineProfile.READ_ONLY: {
        "minimum_plan": "basic_pass",
        "max_ttl": 14400,
        "certificate_required": False,
        "allowed_actions": {
            "cached_metric_read",
            "report_view",
            "evidence_verify",
            "policy_inspect",
            "operational_status_read",
        },
        "device_classes": {"desktop_vault", "mobile_vault", "payregister_device"},
        "max_operations": 500,
        "max_pending_events": 1000,
    },
    OfflineProfile.ANALYST_CACHED: {
        "minimum_plan": "plus_pass",
        "max_ttl": 43200,
        "certificate_required": False,
        "allowed_actions": {
            "cached_metric_read",
            "cached_similarity",
            "local_report_generate",
            "report_view",
            "evidence_verify",
        },
        "device_classes": {"desktop_vault", "mobile_vault"},
        "max_operations": 1000,
        "max_pending_events": 1000,
    },
    OfflineProfile.PAYREGISTER_CASHIER_SHIFT: {
        "minimum_plan": "business_pass",
        "max_ttl": 43200,
        "certificate_required": True,
        "allowed_actions": {
            "payregister_invoice_create",
            "payregister_receipt_create",
            "payregister_shift_close",
            "payment_observation_queue",
        },
        "device_classes": {"payregister_device"},
        "max_operations": 500,
        "max_pending_events": 1000,
    },
    OfflineProfile.BUSINESS_DEGRADED: {
        "minimum_plan": "business_pass",
        "max_ttl": 14400,
        "certificate_required": True,
        "allowed_actions": {
            "business_dashboard_read",
            "operational_status_read",
            "preapproved_operation_queue",
        },
        "device_classes": {"desktop_vault", "payregister_device"},
        "max_operations": 250,
        "max_pending_events": 500,
    },
}


@dataclass(frozen=True, slots=True)
class OfflineOperationDecision:
    allowed: bool
    decision: str
    reason_code: str
    restrictions: tuple[str, ...] = ()


class OfflinePolicyEvaluator:
    def evaluate(
        self,
        pack: dict[str, Any],
        *,
        operation: str,
        device_key_fingerprint: str,
        principal_hash: str,
        local_operation_count: int = 0,
        value_amount: int = 0,
        queued_event_count: int = 0,
        now: datetime | None = None,
        trusted_time_available: bool = True,
        last_trusted_at: datetime | None = None,
    ) -> OfflineOperationDecision:
        now = _utc(now or datetime.now(UTC))
        policy, validity = pack.get("offline_policy", {}), pack.get("validity", {})
        if pack.get("device_binding", {}).get("device_key_fingerprint") != device_key_fingerprint:
            return _deny("device_mismatch")
        if pack.get("principal", {}).get("principal_hash") != principal_hash:
            return _deny("principal_mismatch")
        if operation in FORBIDDEN_OFFLINE_ACTIONS or operation not in set(
            policy.get("allowed_actions", [])
        ):
            return _deny("operation_not_allowed")
        if (
            not trusted_time_available
            and pack.get("offline_policy", {}).get("profile") != "read_only"
        ):
            return _deny("trusted_time_unavailable")
        if last_trusted_at and now < _utc(last_trusted_at):
            return _deny("clock_rollback_detected")
        if now < _parse(validity.get("not_before")) or now >= _parse(validity.get("expires_at")):
            return _deny("expired")
        if (
            _parse(validity.get("issued_at"))
            + timedelta(seconds=int(validity.get("maximum_offline_seconds", 0)))
        ) < now:
            return _deny("maximum_offline_duration_exceeded")
        quota = policy.get("quota", {})
        if local_operation_count >= int(quota.get("maximum_operations", 0)):
            return _deny("quota_exceeded")
        if queued_event_count >= int(
            pack.get("reconciliation", {}).get("maximum_pending_events", 0)
        ):
            return _deny("reconciliation_required")
        limit = int(policy.get("maximum_value_limits", {}).get(operation, 0))
        if value_amount and (limit <= 0 or value_amount > limit):
            return _deny("value_limit_exceeded")
        return OfflineOperationDecision(
            True, "allow_offline", "allowed", ("device_bound", "reconciliation_required")
        )


def _deny(reason: str) -> OfflineOperationDecision:
    return OfflineOperationDecision(False, "deny", reason)


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _parse(value: object) -> datetime:
    if not isinstance(value, str):
        return datetime.min.replace(tzinfo=UTC)
    return _utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
