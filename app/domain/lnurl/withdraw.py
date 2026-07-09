"""LNURL-withdraw domain enums."""

from __future__ import annotations

from enum import StrEnum


class LNURLWithdrawStatus(StrEnum):
    CREATED = "created"
    POLICY_PENDING = "policy_pending"
    POLICY_APPROVED = "policy_approved"
    QR_ISSUED = "qr_issued"
    INVOICE_RECEIVED = "invoice_received"
    PAYMENT_PENDING = "payment_pending"
    PAID = "paid"
    FAILED = "failed"
    EXPIRED = "expired"
    REVOKED = "revoked"


class LNURLWithdrawPurpose(StrEnum):
    SUBSCRIPTION_REFUND = "subscription_refund"
    PAYREGISTER_REFUND = "payregister_refund"
    CASHBACK = "cashback"
    REWARD = "reward"
    BUG_BOUNTY = "bug_bounty"
    PARTNER_PAYOUT = "partner_payout"
    TESTNET_FAUCET = "testnet_faucet"
    SIGNET_FAUCET = "signet_faucet"
