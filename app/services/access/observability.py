"""Shared, non-blocking Prometheus instrumentation for Access security flows."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast
from prometheus_client import REGISTRY, Counter, Gauge, Histogram

from app.services.access.observability_labels import (
    ActorTypeLabel,
    AuthMethodLabel,
    EndpointGroupLabel,
    ReasonCodeLabel,
    ResultLabel,
    normalize_label,
)

DURATION_BUCKETS = (0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30)


def metric_counter(name: str, documentation: str, labels: list[str]) -> Counter:
    return cast(Counter, _metric(Counter, name, documentation, labels))


def metric_gauge(name: str, documentation: str, labels: list[str]) -> Gauge:
    return cast(Gauge, _metric(Gauge, name, documentation, labels))


def metric_histogram(
    name: str, documentation: str, labels: list[str], *, buckets: tuple[float, ...]
) -> Histogram:
    return cast(Histogram, _metric(Histogram, name, documentation, labels, buckets=buckets))


def _metric(
    metric_type: type, name: str, documentation: str, labels: list[str], **kwargs: object
) -> Any:
    """Idempotently reuse a collector registered by reloads or another adapter."""
    existing = getattr(REGISTRY, "_names_to_collectors", {}).get(name)
    if existing is not None:
        return existing
    try:
        return metric_type(name, documentation, labels, **kwargs)
    except ValueError:
        existing = getattr(REGISTRY, "_names_to_collectors", {}).get(name)
        if existing is None:
            raise
        return existing


ACCESS_POLICY_DECISIONS = metric_counter(
    "bastion_access_policy_decisions_total",
    "Central Access policy decisions.",
    ["actor_type", "decision", "reason_code", "action_group"],
)
ACCESS_REVOCATION_CHECKS = metric_counter(
    "bastion_access_revocation_checks_total",
    "Authoritative revocation checks.",
    ["target_type", "result", "reason_code"],
)
ACCESS_RECOVERY_EVENTS = metric_counter(
    "bastion_access_recovery_events_total",
    "Wallet recovery transitions.",
    ["recovery_profile", "result", "reason_code"],
)
ACCESS_AUDIT_APPEND = metric_counter(
    "bastion_access_audit_appends_total",
    "Canonical audit append outcomes.",
    ["event_group", "result", "reason_code"],
)
ACCESS_SECURITY_ALERTS = metric_counter(
    "bastion_access_security_alerts_total",
    "Aggregated Access security alerts.",
    ["alert_type", "severity", "reason_code"],
)
ACCESS_INTEGRITY_BAND = metric_gauge(
    "bastion_access_integrity_band_population",
    "Aggregate current integrity population.",
    ["actor_type", "band", "score_version"],
)


def safe_inc(metric: Counter, labels: Mapping[str, str], amount: float = 1.0) -> None:
    """Metrics are best-effort and can never block security or payment flows."""
    try:
        metric.labels(**dict(labels)).inc(amount)
    except Exception:
        return


def safe_observe(metric: Histogram, labels: Mapping[str, str], value: float) -> None:
    try:
        metric.labels(**dict(labels)).observe(max(0.0, float(value)))
    except Exception:
        return


def safe_set(metric: Gauge, labels: Mapping[str, str], value: float) -> None:
    try:
        metric.labels(**dict(labels)).set(float(value))
    except Exception:
        return


def record_policy_decision(
    *, actor_type: object, decision: object, reason_code: object, action_group: object
) -> None:
    safe_inc(
        ACCESS_POLICY_DECISIONS,
        {
            "actor_type": normalize_label(actor_type, ActorTypeLabel),
            "decision": _bounded(
                decision,
                {
                    "allow",
                    "deny",
                    "step_up_required",
                    "quorum_required",
                    "upgrade_required",
                    "revoked",
                    "expired",
                    "online_check_required",
                    "unknown",
                },
            ),
            "reason_code": normalize_label(reason_code, ReasonCodeLabel),
            "action_group": _bounded(
                action_group, {"routine", "medium", "high", "critical", "sovereign"}
            ),
        },
    )


def wallet_session_labels(
    *, actor_type: object, auth_method: object, plan: object, result: object, reason_code: object
) -> dict[str, str]:
    return {
        "actor_type": normalize_label(actor_type, ActorTypeLabel),
        "auth_method": normalize_label(auth_method, AuthMethodLabel),
        "plan": _bounded(plan, _PLANS),
        "result": normalize_label(result, ResultLabel),
        "reason_code": normalize_label(reason_code, ReasonCodeLabel),
    }


def endpoint_group(path_or_group: object) -> str:
    candidate = str(path_or_group or "").lower()
    if candidate.startswith("/"):
        for marker, group in (
            ("wallet", "wallet_auth"),
            ("lnurl/auth", "lnurl_auth"),
            ("lnurl/pay", "lnurl_pay"),
            ("withdraw", "lnurl_withdraw"),
            ("metric", "metrics"),
            ("trace", "trace"),
            ("treasury", "treasury"),
            ("payregister", "payregister"),
            ("business", "business"),
            ("enterprise", "enterprise"),
            ("recovery", "recovery"),
            ("access", "access"),
        ):
            if marker in candidate:
                return group
        return "unknown"
    return normalize_label(candidate, EndpointGroupLabel)


_PLANS = {
    "lite_pass",
    "basic_pass",
    "plus_pass",
    "pro_pass",
    "business",
    "enterprise",
    "sovereign",
    "unknown",
}


def _bounded(value: object, allowed: set[str]) -> str:
    candidate = str(value or "unknown").strip().lower()
    return candidate if candidate in allowed else "unknown"
