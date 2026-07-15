"""LNURL-withdraw domain primitives."""

from __future__ import annotations

from enum import StrEnum


class LNURLWithdrawStatus(StrEnum):
    CREATED = "created"
    POLICY_PENDING = "policy_pending"
    APPROVED = "approved"
    POLICY_APPROVED = "approved"
    QR_ISSUED = "qr_issued"
    INVOICE_RECEIVED = "invoice_received"
    PAYMENT_QUEUED = "payment_queued"
    PAYMENT_PENDING = "payment_queued"
    PAID = "paid"
    EXPIRED = "expired"
    REJECTED = "rejected"
    FAILED = "failed"
    REVOKED = "revoked"


class LNURLWithdrawPurpose(StrEnum):
    SUBSCRIPTION_REFUND = "subscription_refund"
    PAYREGISTER_REFUND = "payregister_refund"
    CASHBACK = "cashback"
    REWARD = "reward"
    BUG_BOUNTY = "bug_bounty"
    PARTNER_PAYOUT = "partner_payout"
    MERCHANT_PAYOUT = "merchant_payout"
    TESTNET_FAUCET = "testnet_faucet"
    SIGNET_FAUCET = "signet_faucet"


class LNURLWithdrawRiskClass(StrEnum):
    LOW_VALUE = "low_value"
    CONTROLLED = "controlled"
    HIGH_VALUE = "high_value"
    BUSINESS_CRITICAL = "business_critical"


WITHDRAW_REQUIRES_AUTH = frozenset({p for p in LNURLWithdrawPurpose if p not in {LNURLWithdrawPurpose.TESTNET_FAUCET, LNURLWithdrawPurpose.SIGNET_FAUCET}})
WITHDRAW_REQUIRES_STEP_UP = frozenset({LNURLWithdrawRiskClass.HIGH_VALUE, LNURLWithdrawRiskClass.BUSINESS_CRITICAL})
WITHDRAW_REQUIRES_BUSINESS_POLICY = frozenset({LNURLWithdrawPurpose.PAYREGISTER_REFUND, LNURLWithdrawPurpose.PARTNER_PAYOUT, LNURLWithdrawPurpose.MERCHANT_PAYOUT})

_WITHDRAW_TRANSITIONS = {
    LNURLWithdrawStatus.CREATED: frozenset({LNURLWithdrawStatus.POLICY_PENDING, LNURLWithdrawStatus.EXPIRED, LNURLWithdrawStatus.REJECTED, LNURLWithdrawStatus.REVOKED}),
    LNURLWithdrawStatus.POLICY_PENDING: frozenset({LNURLWithdrawStatus.APPROVED, LNURLWithdrawStatus.REJECTED, LNURLWithdrawStatus.EXPIRED}),
    LNURLWithdrawStatus.APPROVED: frozenset({LNURLWithdrawStatus.QR_ISSUED, LNURLWithdrawStatus.EXPIRED, LNURLWithdrawStatus.REVOKED}),
    LNURLWithdrawStatus.QR_ISSUED: frozenset({LNURLWithdrawStatus.INVOICE_RECEIVED, LNURLWithdrawStatus.EXPIRED, LNURLWithdrawStatus.REVOKED}),
    LNURLWithdrawStatus.INVOICE_RECEIVED: frozenset({LNURLWithdrawStatus.PAYMENT_QUEUED, LNURLWithdrawStatus.FAILED, LNURLWithdrawStatus.EXPIRED}),
    LNURLWithdrawStatus.PAYMENT_QUEUED: frozenset({LNURLWithdrawStatus.PAID, LNURLWithdrawStatus.FAILED}),
    LNURLWithdrawStatus.PAID: frozenset(),
    LNURLWithdrawStatus.EXPIRED: frozenset(),
    LNURLWithdrawStatus.REJECTED: frozenset(),
    LNURLWithdrawStatus.FAILED: frozenset(),
    LNURLWithdrawStatus.REVOKED: frozenset(),
}


def can_transition_withdraw(current: LNURLWithdrawStatus | str, target: LNURLWithdrawStatus | str) -> bool:
    return LNURLWithdrawStatus(target) in _WITHDRAW_TRANSITIONS[LNURLWithdrawStatus(current)]


def is_terminal_withdraw_status(status: LNURLWithdrawStatus | str) -> bool:
    return not _WITHDRAW_TRANSITIONS[LNURLWithdrawStatus(status)]


def requires_withdraw_policy(purpose_or_risk: LNURLWithdrawPurpose | LNURLWithdrawRiskClass | str) -> bool:
    value = str(purpose_or_risk)
    return value in {item.value for item in WITHDRAW_REQUIRES_BUSINESS_POLICY | WITHDRAW_REQUIRES_STEP_UP}
