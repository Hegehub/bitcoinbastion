"""Domain values for LNURL-withdraw risk, audit, and execution controls."""

from __future__ import annotations

from enum import StrEnum


class LNURLWithdrawPurpose(StrEnum):
    SUBSCRIPTION_REFUND = "subscription_refund"
    PAYREGISTER_REFUND = "payregister_refund"
    CASHBACK = "cashback"
    CUSTOMER_REWARD = "customer_reward"
    OPERATOR_REWARD = "operator_reward"
    PARTNER_PAYOUT = "partner_payout"
    BUG_BOUNTY = "bug_bounty"
    TESTNET_FAUCET = "testnet_faucet"
    SIGNET_FAUCET = "signet_faucet"
    ADMINISTRATIVE_ADJUSTMENT = "administrative_adjustment"


class LNURLWithdrawRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LNURLWithdrawRiskDecision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    STEP_UP_REQUIRED = "step_up_required"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    COOLDOWN_REQUIRED = "cooldown_required"
    QUOTA_EXCEEDED = "quota_exceeded"
    AMOUNT_EXCEEDED = "amount_exceeded"
    VELOCITY_EXCEEDED = "velocity_exceeded"
    ORIGINAL_PAYMENT_REQUIRED = "original_payment_required"
    DESTINATION_REJECTED = "destination_rejected"
    REVOKED = "revoked"
    LOCKDOWN = "lockdown"


class LNURLWithdrawStatus(StrEnum):
    CREATED = "created"
    POLICY_PENDING = "policy_pending"
    POLICY_DENIED = "policy_denied"
    STEP_UP_REQUIRED = "step_up_required"
    MANUAL_REVIEW = "manual_review"
    APPROVED = "approved"
    QR_ISSUED = "qr_issued"
    INVOICE_RECEIVED = "invoice_received"
    PAYMENT_QUEUED = "payment_queued"
    PAYMENT_IN_FLIGHT = "payment_in_flight"
    PAYMENT_SUCCEEDED = "payment_succeeded"
    SETTLEMENT_CONFIRMED = "settlement_confirmed"
    FAILED_RETRYABLE = "failed_retryable"
    FAILED_TERMINAL = "failed_terminal"
    EXPIRED = "expired"
    REVOKED = "revoked"
    CANCELLED = "cancelled"


class LNURLWithdrawFailureCategory(StrEnum):
    INVALID_K1 = "invalid_k1"
    REUSED_K1 = "reused_k1"
    EXPIRED_K1 = "expired_k1"
    INVALID_INVOICE = "invalid_invoice"
    INVOICE_AMOUNT_MISMATCH = "invoice_amount_mismatch"
    INVOICE_NETWORK_MISMATCH = "invoice_network_mismatch"
    INVOICE_EXPIRED = "invoice_expired"
    INVOICE_ALREADY_PAID = "invoice_already_paid"
    POLICY_DENIED = "policy_denied"
    ACTOR_REVOKED = "actor_revoked"
    SESSION_INVALID = "session_invalid"
    STEP_UP_MISSING = "step_up_missing"
    AMOUNT_LIMIT = "amount_limit"
    VELOCITY_LIMIT = "velocity_limit"
    DUPLICATE_REQUEST = "duplicate_request"
    PROVIDER_ERROR = "provider_error"
    PROVIDER_TIMEOUT = "provider_timeout"
    INSUFFICIENT_LIQUIDITY = "insufficient_liquidity"
    ROUTING_FAILURE = "routing_failure"
    RECONCILIATION_MISMATCH = "reconciliation_mismatch"
    INTERNAL_ERROR = "internal_error"


TERMINAL_WITHDRAW_STATUSES = frozenset(
    {
        LNURLWithdrawStatus.SETTLEMENT_CONFIRMED,
        LNURLWithdrawStatus.FAILED_TERMINAL,
        LNURLWithdrawStatus.EXPIRED,
        LNURLWithdrawStatus.REVOKED,
        LNURLWithdrawStatus.CANCELLED,
    }
)

ALLOWED_WITHDRAW_STATUS_TRANSITIONS: dict[LNURLWithdrawStatus, frozenset[LNURLWithdrawStatus]] = {
    LNURLWithdrawStatus.CREATED: frozenset({LNURLWithdrawStatus.POLICY_PENDING, LNURLWithdrawStatus.CANCELLED}),
    LNURLWithdrawStatus.POLICY_PENDING: frozenset({LNURLWithdrawStatus.APPROVED, LNURLWithdrawStatus.POLICY_DENIED, LNURLWithdrawStatus.STEP_UP_REQUIRED, LNURLWithdrawStatus.MANUAL_REVIEW, LNURLWithdrawStatus.CANCELLED}),
    LNURLWithdrawStatus.STEP_UP_REQUIRED: frozenset({LNURLWithdrawStatus.APPROVED, LNURLWithdrawStatus.POLICY_DENIED, LNURLWithdrawStatus.EXPIRED, LNURLWithdrawStatus.CANCELLED}),
    LNURLWithdrawStatus.MANUAL_REVIEW: frozenset({LNURLWithdrawStatus.APPROVED, LNURLWithdrawStatus.POLICY_DENIED, LNURLWithdrawStatus.CANCELLED}),
    LNURLWithdrawStatus.APPROVED: frozenset({LNURLWithdrawStatus.QR_ISSUED, LNURLWithdrawStatus.REVOKED, LNURLWithdrawStatus.EXPIRED, LNURLWithdrawStatus.CANCELLED}),
    LNURLWithdrawStatus.QR_ISSUED: frozenset({LNURLWithdrawStatus.INVOICE_RECEIVED, LNURLWithdrawStatus.REVOKED, LNURLWithdrawStatus.EXPIRED, LNURLWithdrawStatus.CANCELLED}),
    LNURLWithdrawStatus.INVOICE_RECEIVED: frozenset({LNURLWithdrawStatus.PAYMENT_QUEUED, LNURLWithdrawStatus.POLICY_DENIED, LNURLWithdrawStatus.FAILED_TERMINAL, LNURLWithdrawStatus.REVOKED}),
    LNURLWithdrawStatus.PAYMENT_QUEUED: frozenset({LNURLWithdrawStatus.PAYMENT_IN_FLIGHT, LNURLWithdrawStatus.CANCELLED, LNURLWithdrawStatus.REVOKED}),
    LNURLWithdrawStatus.PAYMENT_IN_FLIGHT: frozenset({LNURLWithdrawStatus.PAYMENT_SUCCEEDED, LNURLWithdrawStatus.FAILED_RETRYABLE, LNURLWithdrawStatus.FAILED_TERMINAL}),
    LNURLWithdrawStatus.PAYMENT_SUCCEEDED: frozenset({LNURLWithdrawStatus.SETTLEMENT_CONFIRMED, LNURLWithdrawStatus.FAILED_RETRYABLE}),
    LNURLWithdrawStatus.FAILED_RETRYABLE: frozenset({LNURLWithdrawStatus.PAYMENT_QUEUED, LNURLWithdrawStatus.FAILED_TERMINAL, LNURLWithdrawStatus.CANCELLED}),
}


def can_transition(from_status: LNURLWithdrawStatus, to_status: LNURLWithdrawStatus) -> bool:
    if from_status == to_status:
        return True
    if from_status in TERMINAL_WITHDRAW_STATUSES:
        return False
    return to_status in ALLOWED_WITHDRAW_STATUS_TRANSITIONS.get(from_status, frozenset())
