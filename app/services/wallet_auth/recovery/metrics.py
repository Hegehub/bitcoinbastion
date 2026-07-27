from app.services.access.observability import (
    DURATION_BUCKETS,
    metric_counter,
    metric_histogram,
    safe_inc,
)

_LABELS = ["recovery_profile", "principal_type", "result", "risk_level", "reason_code"]
RECOVERY_CAPSULES_CREATED = metric_counter(
    "bastion_recovery_capsules_created_total", "Recovery Capsules created.", _LABELS
)
RECOVERY_CAPSULES_COMPLETED = metric_counter(
    "bastion_recovery_capsules_completed_total", "Recovery Capsules completed.", _LABELS
)
RECOVERY_CAPSULES_FAILED = metric_counter(
    "bastion_recovery_capsules_failed_total", "Recovery Capsules failed.", _LABELS
)
RECOVERY_CAPSULES_LOCKED = metric_counter(
    "bastion_recovery_capsules_locked_total", "Recovery Capsules locked.", _LABELS
)
RECOVERY_FACTOR_VERIFIED = metric_counter(
    "bastion_recovery_factor_verified_total",
    "Recovery factors verified.",
    [*_LABELS, "factor_type"],
)
RECOVERY_FACTOR_REJECTED = metric_counter(
    "bastion_recovery_factor_rejected_total",
    "Recovery factors rejected.",
    [*_LABELS, "factor_type"],
)
RECOVERY_REPLAY_REJECTED = metric_counter(
    "bastion_recovery_replay_rejected_total", "Recovery replay attempts rejected.", _LABELS
)
RECOVERY_COOLDOWN_STARTED = metric_counter(
    "bastion_recovery_cooldown_started_total", "Recovery cooldowns started.", _LABELS
)
RECOVERY_COOLDOWN_EXTENDED = metric_counter(
    "bastion_recovery_cooldown_extended_total", "Recovery cooldowns extended.", _LABELS
)
RECOVERY_POLICY_DENIED = metric_counter(
    "bastion_recovery_policy_denied_total", "Recovery policy denials.", _LABELS
)
RECOVERY_DURATION = metric_histogram(
    "bastion_recovery_duration_seconds",
    "Recovery duration.",
    ["recovery_profile", "principal_type", "result"],
    buckets=DURATION_BUCKETS,
)

_PROFILES = {"lite_basic", "plus", "pro", "business", "enterprise", "sovereign", "unknown"}
_PRINCIPALS = {"bitcoin_wallet_principal", "lightning_wallet_principal", "unknown"}
_RESULTS = {"success", "failed", "rejected", "locked", "denied", "pending", "unknown"}
_RISK = {"low", "medium", "high", "critical", "unknown"}
_REASONS = {
    "created",
    "completed",
    "factor_verified",
    "factor_rejected",
    "replay_detected",
    "cooldown_started",
    "cooldown_extended",
    "policy_denied",
    "attempts_exceeded",
    "revoked",
    "expired",
    "unknown",
}


def _bounded(value: object, allowed: set[str]) -> str:
    candidate = str(value or "unknown").lower()
    return candidate if candidate in allowed else "unknown"


class RecoveryMetrics:
    _METRICS = {
        metric._name: metric
        for metric in (
            RECOVERY_CAPSULES_CREATED,
            RECOVERY_CAPSULES_COMPLETED,
            RECOVERY_CAPSULES_FAILED,
            RECOVERY_CAPSULES_LOCKED,
            RECOVERY_REPLAY_REJECTED,
            RECOVERY_COOLDOWN_STARTED,
            RECOVERY_COOLDOWN_EXTENDED,
            RECOVERY_POLICY_DENIED,
        )
    }

    def emit(self, name: str, labels: dict[str, str]) -> None:
        metric = self._METRICS.get(name.removesuffix("_total"))
        if metric is None:
            return
        safe_inc(
            metric,
            {
                "recovery_profile": _bounded(labels.get("recovery_profile"), _PROFILES),
                "principal_type": _bounded(labels.get("principal_type"), _PRINCIPALS),
                "result": _bounded(labels.get("result"), _RESULTS),
                "risk_level": _bounded(labels.get("risk_level"), _RISK),
                "reason_code": _bounded(labels.get("reason_code"), _REASONS),
            },
        )
