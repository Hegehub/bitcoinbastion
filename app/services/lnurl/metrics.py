"""Low-cardinality LNURL metrics hooks used by service tests and adapters."""
from __future__ import annotations

from dataclasses import dataclass, field

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
ALLOWED_LABELS = {"purpose", "network", "status", "decision", "risk_level", "failure_category", "provider"}
FORBIDDEN_LABELS = {"principal_hash", "merchant_hash", "wallet_key", "invoice", "payment_hash", "k1", "session", "device_fingerprint", "withdraw_request_id"}
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

    def record(self, name: str, labels: dict[str, str] | None = None, value: float = 1.0) -> MetricEvent:
        labels = labels or {}
        illegal = (set(labels) - ALLOWED_LABELS) | (set(labels) & FORBIDDEN_LABELS)
        if illegal:
            raise ValueError(f"forbidden or high-cardinality metric labels: {sorted(illegal)}")
        event = MetricEvent(name=name, labels=dict(labels), value=value)
        self.events.append(event)
        return event
