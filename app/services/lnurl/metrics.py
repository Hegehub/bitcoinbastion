"""Low-cardinality LNURL metrics hooks used by service tests and adapters."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.services.access.observability import (
    DURATION_BUCKETS,
    metric_counter,
    metric_histogram,
    safe_inc,
    safe_observe,
)
from app.services.access.observability_labels import ReasonCodeLabel, ResultLabel, normalize_label

LNURL_WITHDRAW_METRICS = (
    "bastion_lnurl_withdraw_requests_total",
    "bastion_lnurl_withdraw_requested_msat_total",
    "bastion_lnurl_withdraw_approved_total",
    "bastion_lnurl_withdraw_denied_total",
    "bastion_lnurl_withdraw_step_up_total",
    "bastion_lnurl_withdraw_manual_review_total",
    "bastion_lnurl_withdraw_velocity_rejected_total",
    "bastion_lnurl_withdraw_invoice_rejected_total",
    "bastion_lnurl_withdraw_payment_attempts_total",
    "bastion_lnurl_withdraw_payment_succeeded_total",
    "bastion_lnurl_withdraw_payment_failed_total",
    "bastion_lnurl_withdraw_payment_in_flight",
    "bastion_lnurl_withdraw_reconciliation_mismatch_total",
    "bastion_lnurl_withdraw_amount_msat",
    "bastion_lnurl_withdraw_latency_seconds",
)
ALLOWED_LABELS = {
    "purpose",
    "network",
    "status",
    "decision",
    "risk_level",
    "failure_category",
    "provider",
}
FORBIDDEN_LABELS = {
    "principal_hash",
    "merchant_hash",
    "wallet_key",
    "invoice",
    "payment_hash",
    "k1",
    "session",
    "device_fingerprint",
    "withdraw_request_id",
}
ALERT_RECOMMENDATIONS = (
    "sudden_payout_amount_spike",
    "high_failure_rate",
    "replay_attempts",
    "velocity_denials",
    "reconciliation_mismatch",
    "provider_timeout_increase",
    "unexpected_mainnet_payout_activity",
    "manual_review_backlog",
)


@dataclass(frozen=True)
class MetricEvent:
    name: str
    labels: dict[str, str]
    value: float = 1.0


@dataclass
class LNURLWithdrawMetrics:
    events: list[MetricEvent] = field(default_factory=list)

    def record(
        self, name: str, labels: dict[str, str] | None = None, value: float = 1.0
    ) -> MetricEvent:
        labels = labels or {}
        illegal = (set(labels) - ALLOWED_LABELS) | (set(labels) & FORBIDDEN_LABELS)
        if illegal:
            raise ValueError(f"forbidden or high-cardinality metric labels: {sorted(illegal)}")
        event = MetricEvent(name=name, labels=dict(labels), value=value)
        self.events.append(event)
        return event


LNURL_AUTH_CHALLENGES = metric_counter(
    "lnurl_auth_challenges_total",
    "LNURL-auth challenge outcomes.",
    ["action", "result", "reason_code"],
)
LNURL_AUTH_CALLBACKS = metric_counter(
    "lnurl_auth_callbacks_total",
    "LNURL-auth callback outcomes.",
    ["action", "result", "reason_code", "wallet_compatibility_class"],
)
LNURL_AUTH_SIGNATURES = metric_counter(
    "lnurl_auth_signature_verifications_total",
    "LNURL-auth signature checks.",
    ["action", "verification_strength", "result", "reason_code"],
)
LNURL_AUTH_K1_EVENTS = metric_counter(
    "lnurl_auth_k1_events_total",
    "LNURL k1 lifecycle events.",
    ["flow", "event", "result", "reason_code"],
)
LNURL_AUTH_DURATION = metric_histogram(
    "lnurl_auth_duration_seconds",
    "LNURL-auth flow duration.",
    ["action", "result"],
    buckets=DURATION_BUCKETS,
)
LNURL_PAY_REQUESTS = metric_counter(
    "lnurl_pay_requests_total", "LNURL-pay request outcomes.", ["plan", "result", "reason_code"]
)
LNURL_PAY_INVOICES = metric_counter(
    "lnurl_pay_invoices_total", "LNURL-pay invoice outcomes.", ["plan", "result", "reason_code"]
)
LNURL_PAYMENT_STATES = metric_counter(
    "lnurl_payment_state_transitions_total",
    "Verified payment state transitions.",
    ["payment_method", "from_state", "to_state", "result", "reason_code"],
)
LNURL_VERIFY = metric_counter(
    "lnurl_verify_total",
    "LNURL verification outcomes.",
    ["verification_method", "result", "reason_code"],
)
LNURL_VERIFY_DURATION = metric_histogram(
    "lnurl_verify_duration_seconds",
    "LNURL verification duration.",
    ["verification_method", "result"],
    buckets=DURATION_BUCKETS,
)
LIGHTNING_ADDRESS_RESOLUTIONS = metric_counter(
    "lightning_address_resolutions_total",
    "Lightning Address aggregate resolution outcomes.",
    ["address_class", "domain_class", "result", "reason_code"],
)
LNURL_WITHDRAW_REQUESTS = metric_counter(
    "lnurl_withdraw_requests_total",
    "LNURL-withdraw outcomes.",
    ["stage", "payout_class", "result", "reason_code"],
)
LNURL_WITHDRAW_DURATION = metric_histogram(
    "lnurl_withdraw_duration_seconds",
    "LNURL-withdraw stage duration.",
    ["stage", "result"],
    buckets=DURATION_BUCKETS,
)
LNURL_ENTITLEMENTS = metric_counter(
    "lnurl_payment_entitlements_total",
    "Payment-to-entitlement outcomes.",
    ["plan", "payment_state", "result", "reason_code"],
)
LNURL_PAYERDATA = metric_counter(
    "lnurl_payerdata_events_total",
    "Privacy-minimized payerData outcomes.",
    ["field_class", "result", "reason_code"],
)
LNURL_SUCCESS_ACTIONS = metric_counter(
    "lnurl_success_actions_total",
    "LNURL successAction outcomes.",
    ["action_type", "result", "reason_code"],
)
_POLICY_LABELS = [
    "action_category",
    "decision",
    "reason_category",
    "actor_type",
    "verification_strength",
    "environment",
]
LNURL_POLICY_DECISIONS = metric_counter(
    "bastion_lnurl_policy_decisions_total", "LNURL central policy decisions.", _POLICY_LABELS
)
LNURL_POLICY_DENIALS = metric_counter(
    "bastion_lnurl_policy_denials_total", "LNURL central policy denials.", _POLICY_LABELS
)
LNURL_ENTITLEMENT_DENIED = metric_counter(
    "bastion_lnurl_entitlement_denied_total", "LNURL entitlement policy denials.", _POLICY_LABELS
)
LNURL_WITHDRAW_DENIED = metric_counter(
    "bastion_lnurl_withdraw_denied_total", "LNURL withdraw policy denials.", _POLICY_LABELS
)
LNURL_POLICY_STEP_UP = metric_counter(
    "bastion_lnurl_policy_step_up_total", "LNURL policy step-up requirements.", _POLICY_LABELS
)
LNURL_POLICY_QUORUM = metric_counter(
    "bastion_lnurl_policy_quorum_required_total",
    "LNURL policy quorum requirements.",
    _POLICY_LABELS,
)

_RECOVERY_LABELS = [
    "recovery_profile",
    "verification_strength",
    "decision",
    "reason_code",
    "environment",
]
LNURL_RECOVERY_METRICS = {
    name: metric_counter(
        name, "Privacy-preserving LNURL Recovery Capsule outcome.", _RECOVERY_LABELS
    )
    for name in (
        "bastion_lnurl_recovery_factor_requested_total",
        "bastion_lnurl_recovery_factor_verified_total",
        "bastion_lnurl_recovery_factor_failed_total",
        "bastion_lnurl_recovery_k1_reused_total",
        "bastion_lnurl_recovery_k1_expired_total",
        "bastion_lnurl_recovery_principal_mismatch_total",
        "bastion_lnurl_recovery_rate_limited_total",
        "bastion_lnurl_recovery_policy_denied_total",
    )
}

_ACTIONS = {"register", "login", "link", "auth", "unknown"}
_COMPAT = {"native", "compatible", "legacy", "unknown"}
_STRENGTH = {"compatibility", "standard", "high_assurance", "sovereign", "unknown"}
_FLOWS = {"auth", "pay", "withdraw", "payerdata", "step_up", "unknown"}
_K1_EVENTS = {"issued", "consumed", "expired", "revoked", "replay_detected", "invalid", "unknown"}
_PLANS = {"lite_pass", "basic_pass", "plus_pass", "pro_pass", "business", "enterprise", "unknown"}
_PAYMENT_METHODS = {
    "lnurl_pay",
    "lightning_address",
    "lightning_invoice",
    "btcpay",
    "onchain_btc",
    "manual_grant",
    "unknown",
}
_PAYMENT_STATES = {
    "created",
    "invoice_issued",
    "pending",
    "settled",
    "verified",
    "proof_created",
    "entitlement_issued",
    "expired",
    "failed",
    "unknown",
}
_VERIFY_METHODS = {"node", "btcpay", "provider", "internal", "unknown"}
_ADDRESS_CLASSES = {
    "public_product",
    "merchant",
    "payregister_store",
    "payregister_terminal",
    "unknown",
}
_DOMAIN_CLASSES = {"canonical", "custom_verified", "onion", "unknown"}
_WITHDRAW_STAGES = {
    "request_creation",
    "invoice_acceptance",
    "payment_execution",
    "cancel",
    "unknown",
}
_PAYOUT_CLASSES = {"refund", "partner", "reward", "withdraw", "unknown"}


def _label(value: object, allowed: set[str]) -> str:
    candidate = str(value or "unknown").lower()
    return candidate if candidate in allowed else "unknown"


class _LNURLAuthMetrics:
    def auth_callback(
        self,
        *,
        action: object,
        result: object,
        reason_code: object,
        compatibility_class: object,
        duration_seconds: float | None = None,
    ) -> None:
        labels = {
            "action": _label(action, _ACTIONS),
            "result": normalize_label(result, ResultLabel),
            "reason_code": normalize_label(reason_code, ReasonCodeLabel),
            "wallet_compatibility_class": _label(compatibility_class, _COMPAT),
        }
        safe_inc(LNURL_AUTH_CALLBACKS, labels)
        if duration_seconds is not None:
            safe_observe(
                LNURL_AUTH_DURATION,
                {"action": labels["action"], "result": labels["result"]},
                duration_seconds,
            )


class LNURLMetrics(_LNURLAuthMetrics):
    """Adapter compatible with ``LNURLPolicyHooks``' existing metrics protocol."""

    _METRICS = {
        "bastion_lnurl_policy_decisions_total": LNURL_POLICY_DECISIONS,
        "bastion_lnurl_policy_denials_total": LNURL_POLICY_DENIALS,
        "bastion_lnurl_entitlement_denied_total": LNURL_ENTITLEMENT_DENIED,
        "bastion_lnurl_withdraw_denied_total": LNURL_WITHDRAW_DENIED,
        "bastion_lnurl_policy_step_up_total": LNURL_POLICY_STEP_UP,
        "bastion_lnurl_policy_quorum_required_total": LNURL_POLICY_QUORUM,
    }
    _ALLOWED = {
        "action_category": {
            "authentication",
            "payment",
            "entitlement",
            "address",
            "withdraw",
            "metadata",
            "payregister",
            "unknown",
        },
        "decision": {
            "allow",
            "deny",
            "step_up_required",
            "quorum_required",
            "upgrade_required",
            "revoked",
            "expired",
            "unknown",
        },
        "reason_category": {
            "allowed",
            "authentication",
            "payment",
            "revocation",
            "entitlement",
            "role",
            "resource",
            "step_up",
            "quorum",
            "internal",
            "unknown",
        },
        "actor_type": {
            "bitcoin_wallet_principal",
            "lightning_wallet_principal",
            "wallet_device",
            "access_certificate",
            "child_api_key",
            "delegated_pass",
            "business_role",
            "payregister_device",
            "bot",
            "unknown",
        },
        "verification_strength": {
            "compatibility",
            "standard",
            "high_assurance",
            "sovereign",
            "unknown",
        },
        "environment": {"production", "staging", "development", "test", "unknown"},
    }

    def record(
        self, name: str, labels: dict[str, str] | None = None, value: float = 1.0
    ) -> MetricEvent:
        metric = self._METRICS.get(name)
        if metric is None:
            return MetricEvent(name=name, labels={}, value=value)
        supplied = labels or {}
        normalized = {
            key: _label(supplied.get(key), allowed) for key, allowed in self._ALLOWED.items()
        }
        safe_inc(metric, normalized, value)
        return MetricEvent(name=name, labels=normalized, value=value)

    def k1_event(self, *, flow: object, event: object, result: object, reason_code: object) -> None:
        safe_inc(
            LNURL_AUTH_K1_EVENTS,
            {
                "flow": _label(flow, _FLOWS),
                "event": _label(event, _K1_EVENTS),
                "result": normalize_label(result, ResultLabel),
                "reason_code": normalize_label(reason_code, ReasonCodeLabel),
            },
        )

    def payment_transition(
        self,
        *,
        payment_method: object,
        from_state: object,
        to_state: object,
        result: object,
        reason_code: object,
    ) -> None:
        safe_inc(
            LNURL_PAYMENT_STATES,
            {
                "payment_method": _label(payment_method, _PAYMENT_METHODS),
                "from_state": _label(from_state, _PAYMENT_STATES),
                "to_state": _label(to_state, _PAYMENT_STATES),
                "result": normalize_label(result, ResultLabel),
                "reason_code": normalize_label(reason_code, ReasonCodeLabel),
            },
        )

    def address_resolution(
        self, *, address_class: object, domain_class: object, result: object, reason_code: object
    ) -> None:
        safe_inc(
            LIGHTNING_ADDRESS_RESOLUTIONS,
            {
                "address_class": _label(address_class, _ADDRESS_CLASSES),
                "domain_class": _label(domain_class, _DOMAIN_CLASSES),
                "result": normalize_label(result, ResultLabel),
                "reason_code": normalize_label(reason_code, ReasonCodeLabel),
            },
        )

    def withdraw(
        self,
        *,
        stage: object,
        payout_class: object,
        result: object,
        reason_code: object,
        duration_seconds: float | None = None,
    ) -> None:
        labels = {
            "stage": _label(stage, _WITHDRAW_STAGES),
            "payout_class": _label(payout_class, _PAYOUT_CLASSES),
            "result": normalize_label(result, ResultLabel),
            "reason_code": normalize_label(reason_code, ReasonCodeLabel),
        }
        safe_inc(LNURL_WITHDRAW_REQUESTS, labels)
        if duration_seconds is not None:
            safe_observe(
                LNURL_WITHDRAW_DURATION,
                {"stage": labels["stage"], "result": labels["result"]},
                duration_seconds,
            )


class PrometheusLNURLPolicyMetricsSink(LNURLMetrics):
    """Semantic alias used by the central LNURL Policy Hooks."""


class LNURLRecoveryMetrics:
    """Bounded-label adapter for recovery-factor service instrumentation."""

    _PROFILES = {"lite_basic", "plus", "pro", "business", "enterprise", "sovereign"}
    _DECISIONS = {"allow", "deny", "pending", "unknown"}
    _REASONS = {
        "requested",
        "verified",
        "rate_limited",
        "k1_reused",
        "k1_expired",
        "principal_mismatch",
        "policy_denied",
        "revoked",
        "invalid_signature",
        "recovery_unavailable",
        "unknown",
    }

    def record(self, name: str, labels: dict[str, str]) -> None:
        metric = LNURL_RECOVERY_METRICS.get(name)
        if metric is None:
            return
        safe_inc(
            metric,
            {
                "recovery_profile": _label(labels.get("recovery_profile"), self._PROFILES),
                "verification_strength": _label(labels.get("verification_strength"), _STRENGTH),
                "decision": _label(labels.get("decision"), self._DECISIONS),
                "reason_code": _label(labels.get("reason_code"), self._REASONS),
                "environment": _label(
                    labels.get("environment"),
                    {"production", "staging", "development", "test", "unknown"},
                ),
            },
        )
