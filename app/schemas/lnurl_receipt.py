"""Schemas for tamper-evident LNURL Receipt Packets.

An LNURL Receipt Packet is payment evidence. It is not an authentication
credential, Access Pass, Subscription Entitlement, wallet-control proof, or
legal identity proof.
"""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class LNURLReceiptType(StrEnum):
    SUBSCRIPTION_PAYMENT = "subscription_payment"
    PRODUCT_PAYMENT = "product_payment"
    PAYREGISTER_SALE = "payregister_sale"
    PAYREGISTER_INVOICE = "payregister_invoice"
    MERCHANT_LIGHTNING_ADDRESS_PAYMENT = "merchant_lightning_address_payment"
    CONTRIBUTION = "contribution"
    REFUND_REFERENCE = "refund_reference"
    PAYOUT_REFERENCE = "payout_reference"
    TESTNET_PAYMENT = "testnet_payment"


class LNURLReceiptVisibility(StrEnum):
    PRIVATE = "private"
    CUSTOMER = "customer"
    MERCHANT = "merchant"
    BUSINESS_AUDIT = "business_audit"
    ENTERPRISE_EVIDENCE = "enterprise_evidence"
    PUBLIC_REDACTED = "public_redacted"


class LNURLReceiptSettlementEvidence(BaseModel):
    lnurl_pay_request_hash: str
    lnurl_callback_hash: str
    payment_proof_hash: str
    payment_hash: str
    invoice_hash: str
    amount_msat: int = Field(ge=1)
    amount_sats: int = Field(ge=0)
    currency: str = "BTC"
    settlement_method: Literal["lnurl_verify", "internal_lightning_node", "btcpay_webhook", "payment_provider_callback", "preimage_verification", "manual_test_settlement"]
    settled: bool
    preimage_hash: str | None = None
    metadata_hash: str
    comment_hash: str | None = None
    payer_data_hash: str | None = None


class LNURLReceiptPaymentContext(BaseModel):
    product_code: str | None = None
    lightning_address_hash: str | None = None
    lightning_address_alias: str | None = None
    payment_context_hash: str | None = None
    success_action_type: str | None = None
    success_action_hash: str | None = None
    activation_reference_hash: str | None = None
    safe_description: str | None = None


class LNURLReceiptSubscriptionContext(BaseModel):
    plan_code: str
    entitlement_hash: str
    entitlement_status: str
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    activation_state: str | None = None
    metric_entitlement_hash: str | None = None
    limits_hash: str | None = None


class LNURLReceiptMerchantContext(BaseModel):
    workspace_alias: str | None = None
    store_alias: str | None = None
    terminal_alias: str | None = None
    cashier_role_alias: str | None = None
    shift_alias: str | None = None
    order_reference_hash: str | None = None
    merchant_invoice_hash: str | None = None
    receipt_reference_hash: str | None = None
    refund_policy_hash: str | None = None


class LNURLReceiptPrincipalContext(BaseModel):
    principal_type: str | None = None
    principal_alias: str | None = None
    proof_method: str | None = None
    linked_payment_auth: bool = False


class LNURLReceiptPolicyContext(BaseModel):
    decision: Literal["allow", "deny", "step_up_required"]
    policy_hash: str
    policy_epoch: int = 1
    decision_event_hash: str


class LNURLReceiptAuditContext(BaseModel):
    payment_settled_event_hash: str
    payment_proof_event_hash: str
    entitlement_event_hash: str | None = None
    receipt_created_event_hash: str


class LNURLReceiptIssuerSignature(BaseModel):
    issuer_key_id: str
    signature_suite: str
    signature: str | None = None
    crypto_epoch: int = 1
    pq_signature: str | None = None
    public_key_fingerprint: str | None = None
    unsigned: bool = False


class LNURLReceiptPacket(BaseModel):
    type: Literal["bastion_lnurl_receipt_packet"] = "bastion_lnurl_receipt_packet"
    version: int = 1
    schema_epoch: int = 1
    crypto_epoch: int = 1
    receipt_id: str
    receipt_type: LNURLReceiptType
    visibility: LNURLReceiptVisibility = LNURLReceiptVisibility.PRIVATE
    network: str
    created_at: datetime
    settled_at: datetime | None = None
    payment: LNURLReceiptSettlementEvidence
    payment_context: LNURLReceiptPaymentContext | None = None
    subscription: LNURLReceiptSubscriptionContext | None = None
    principal: LNURLReceiptPrincipalContext | None = None
    merchant: LNURLReceiptMerchantContext | None = None
    policy: LNURLReceiptPolicyContext
    audit: LNURLReceiptAuditContext
    issuer: LNURLReceiptIssuerSignature
    packet_hash: str


class LNURLReceiptPublicView(BaseModel):
    receipt_id: str
    receipt_type: LNURLReceiptType
    visibility: LNURLReceiptVisibility
    network: str
    amount_msat: int | None = None
    amount_sats: int | None = None
    currency: str = "BTC"
    settled: bool
    settled_at: datetime | None = None
    safe_description: str | None = None
    entitlement_status: str | None = None
    valid_until: datetime | None = None
    order_reference_hash: str | None = None
    terminal_alias: str | None = None
    shift_alias: str | None = None
    policy_decision: str | None = None
    audit_reference: str | None = None
    issuer_key_id: str | None = None
    packet_hash: str


class LNURLReceiptVerificationResult(BaseModel):
    valid: bool
    packet_hash_valid: bool
    issuer_signature_valid: bool
    settlement_evidence_valid: bool
    context_consistent: bool
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


__all__ = [
    "LNURLReceiptAuditContext",
    "LNURLReceiptIssuerSignature",
    "LNURLReceiptMerchantContext",
    "LNURLReceiptPacket",
    "LNURLReceiptPaymentContext",
    "LNURLReceiptPolicyContext",
    "LNURLReceiptPrincipalContext",
    "LNURLReceiptPublicView",
    "LNURLReceiptSettlementEvidence",
    "LNURLReceiptSubscriptionContext",
    "LNURLReceiptType",
    "LNURLReceiptVerificationResult",
    "LNURLReceiptVisibility",
]
