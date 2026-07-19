"""Domain objects for Bastion LNURL Payment Proofs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


class LNURLPaymentContext(StrEnum):
    SUBSCRIPTION = "subscription"
    SUBSCRIPTION_RENEWAL = "subscription_renewal"
    SUBSCRIPTION_UPGRADE = "subscription_upgrade"
    BUSINESS_INVOICE = "business_invoice"
    ENTERPRISE_INVOICE = "enterprise_invoice"
    PAYREGISTER_PAYMENT = "payregister_payment"
    MERCHANT_PAYMENT = "merchant_payment"
    CONTRIBUTION = "contribution"
    REFUND_REPAYMENT = "refund_repayment"
    TEST_PAYMENT = "test_payment"


class LNURLSettlementMethod(StrEnum):
    INTERNAL_LIGHTNING_NODE = "internal_lightning_node"
    BTCPAY = "btcpay"
    LIGHTNING_PROVIDER = "lightning_provider"
    LNURL_VERIFY = "lnurl_verify"
    PREIMAGE_VERIFICATION = "preimage_verification"
    TEST_SETTLEMENT = "test_settlement"


class LNURLPaymentProofStatus(StrEnum):
    ISSUED = "issued"
    REVOKED = "revoked"
    SUPERSEDED = "superseded"
    DISPUTED = "disputed"


class LNURLPrincipalBindingMethod(StrEnum):
    EXISTING_POP_SESSION = "existing_pop_session"
    VERIFIED_LNURL_AUTH = "verified_lnurl_auth"
    VERIFIED_PAYERDATA_AUTH = "verified_payerdata_auth"
    BUSINESS_WORKSPACE_CONTEXT = "business_workspace_context"
    PAYREGISTER_TERMINAL_CONTEXT = "payregister_terminal_context"
    UNBOUND_PAYMENT = "unbound_payment"


@dataclass(frozen=True, slots=True)
class LNURLIssuerSignature:
    alg: str
    key_id: str
    sig: str

    def as_dict(self) -> dict[str, str]:
        return {"alg": self.alg, "key_id": self.key_id, "sig": self.sig}


@dataclass(frozen=True, slots=True)
class LNURLPaymentProof:
    type: str
    version: int
    proof_id: str
    payment_request_id: str
    payment_hash: str
    invoice_hash: str
    lnurl_callback_hash: str
    verify_reference_hash: str
    payment_context: str
    product_code: str
    amount_msat: int
    currency: str
    network: str
    settled: bool
    settlement_method: str
    settled_at: datetime
    verification_timestamp: datetime
    payment_metadata_hash: str
    issuer_key_id: str
    crypto_epoch: int
    schema_epoch: int
    policy_epoch: int
    created_at: datetime
    proof_fingerprint: str
    issuer_signature: LNURLIssuerSignature
    principal_hash: str | None = None
    principal_type: str | None = None
    binding_method: str = LNURLPrincipalBindingMethod.UNBOUND_PAYMENT.value
    binding_verification_hash: str | None = None
    payer_data_hash: str | None = None
    preimage_commitment: str | None = None
    receipt_reference_hash: str | None = None
    comment_present: bool = False
    comment_hash: str | None = None
    comment_classification: str | None = None
    audit_event_hash: str | None = None
    status: str = LNURLPaymentProofStatus.ISSUED.value
    revoked_at: datetime | None = None

    def unsigned_payload(self) -> dict[str, Any]:
        payload = {
            "type": self.type,
            "version": self.version,
            "proof_id": self.proof_id,
            "payment_request_id": self.payment_request_id,
            "payment_hash": self.payment_hash,
            "invoice_hash": self.invoice_hash,
            "lnurl_callback_hash": self.lnurl_callback_hash,
            "verify_reference_hash": self.verify_reference_hash,
            "principal_hash": self.principal_hash,
            "principal_type": self.principal_type,
            "binding_method": self.binding_method,
            "binding_verification_hash": self.binding_verification_hash,
            "payment_context": self.payment_context,
            "product_code": self.product_code,
            "amount_msat": self.amount_msat,
            "currency": self.currency,
            "network": self.network,
            "settled": self.settled,
            "settlement_method": self.settlement_method,
            "settled_at": self.settled_at.isoformat().replace("+00:00", "Z"),
            "verification_timestamp": self.verification_timestamp.isoformat().replace("+00:00", "Z"),
            "payment_metadata_hash": self.payment_metadata_hash,
            "payer_data_hash": self.payer_data_hash,
            "preimage_commitment": self.preimage_commitment,
            "receipt_reference_hash": self.receipt_reference_hash,
            "comment_present": True if self.comment_hash else None,
            "comment_hash": self.comment_hash,
            "comment_classification": self.comment_classification,
            "issuer_key_id": self.issuer_key_id,
            "crypto_epoch": self.crypto_epoch,
            "schema_epoch": self.schema_epoch,
            "policy_epoch": self.policy_epoch,
            "created_at": self.created_at.isoformat().replace("+00:00", "Z"),
        }
        return {k: v for k, v in payload.items() if v is not None}

    def safe_response(self) -> dict[str, Any]:
        return {
            "proof_id": self.proof_id,
            "type": self.type,
            "version": self.version,
            "payment_context": self.payment_context,
            "product_code": self.product_code,
            "amount_msat": self.amount_msat,
            "currency": self.currency,
            "network": self.network,
            "settled": self.settled,
            "settled_at": self.settled_at.isoformat().replace("+00:00", "Z"),
            "settlement_method": self.settlement_method,
            "principal_bound": self.principal_hash is not None,
            "proof_fingerprint": self.proof_fingerprint,
            "issuer_signature": self.issuer_signature.as_dict(),
            "audit_event_hash": self.audit_event_hash,
        }
