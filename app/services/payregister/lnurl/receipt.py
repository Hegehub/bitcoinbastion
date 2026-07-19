"""PayRegister LNURL receipt records."""
from __future__ import annotations

import secrets
from dataclasses import dataclass, replace
from datetime import datetime

from app.services.access.crypto.hashing import hmac_sha256_prefixed, sha256_prefixed
from app.services.payregister.lnurl.errors import PayRegisterLNURLSettlementError
from app.services.payregister.lnurl.payment_context import PayRegisterLNURLContextStatus
from app.services.payregister.lnurl.static_endpoint import PayRegisterLNURLStaticEndpointService


@dataclass(frozen=True, slots=True)
class PayRegisterLNURLPaymentProof:
    proof_type: str
    version: int
    payment_context_hash: str
    public_endpoint_hash: str
    merchant_workspace_hash: str
    store_hash: str
    terminal_hash: str | None
    invoice_hash: str
    payment_hash: str
    metadata_hash: str
    amount_msat: int
    settlement_method: str
    settled_at: datetime
    audit_event_hash: str
    proof_fingerprint: str


@dataclass(frozen=True, slots=True)
class PayRegisterLNURLReceipt:
    receipt_id: str
    receipt_reference: str
    receipt_reference_hash: str
    merchant_display_label: str
    store_display_label: str
    terminal_display_label: str | None
    order_reference_hash: str | None
    amount_msat: int
    invoice_hash_fingerprint: str
    payment_hash_fingerprint: str
    settled_at: datetime
    metadata_hash: str
    payment_proof_fingerprint: str
    audit_event_hash: str
    refund_status: str


class PayRegisterLNURLReceiptService:
    def __init__(self, *, endpoint_service: PayRegisterLNURLStaticEndpointService, receipt_reference_pepper: str = "dev-payregister-lnurl-receipt-pepper-change-me") -> None:
        self.endpoint_service = endpoint_service
        self.receipt_reference_pepper = receipt_reference_pepper
        self.receipts_by_context_id: dict[str, PayRegisterLNURLReceipt] = {}
        self.proofs_by_context_id: dict[str, PayRegisterLNURLPaymentProof] = {}

    def create_after_settlement(self, context_id: str, *, settlement_method: str = "trusted_test_settlement") -> tuple[PayRegisterLNURLPaymentProof, PayRegisterLNURLReceipt]:
        existing_receipt = self.receipts_by_context_id.get(context_id)
        existing_proof = self.proofs_by_context_id.get(context_id)
        if existing_receipt and existing_proof:
            return existing_proof, existing_receipt
        context = self.endpoint_service.repository.get_context(context_id)
        if context is None or context.status != PayRegisterLNURLContextStatus.SETTLED or not context.settled_at:
            raise PayRegisterLNURLSettlementError("Receipt requires settled PayRegister payment")
        if not context.invoice_hash or not context.payment_hash or context.amount_msat is None and context.min_sendable_msat != context.max_sendable_msat:
            raise PayRegisterLNURLSettlementError("Settled context is missing immutable payment fields")
        amount = context.amount_msat or context.min_sendable_msat
        audit_hash = self.endpoint_service.repository.append_audit("payregister_lnurl_receipt_created", {"context_hash": sha256_prefixed(context_id), "metadata_hash": context.metadata_hash})
        proof_fingerprint = sha256_prefixed(f"{context.payment_context_id}:{context.invoice_hash}:{context.payment_hash}:{amount}")
        proof = PayRegisterLNURLPaymentProof(
            proof_type="bastion_payregister_lnurl_payment_proof",
            version=1,
            payment_context_hash=sha256_prefixed(context.payment_context_id),
            public_endpoint_hash=context.public_endpoint_hash,
            merchant_workspace_hash=context.merchant_workspace_hash,
            store_hash=context.store_hash,
            terminal_hash=context.terminal_hash,
            invoice_hash=context.invoice_hash,
            payment_hash=context.payment_hash,
            metadata_hash=context.metadata_hash,
            amount_msat=amount,
            settlement_method=settlement_method,
            settled_at=context.settled_at,
            audit_event_hash=audit_hash,
            proof_fingerprint=proof_fingerprint,
        )
        reference = f"prr_{secrets.token_urlsafe(24)}"
        receipt = PayRegisterLNURLReceipt(
            receipt_id=f"BPR-{context.settled_at:%Y%m%d}-{len(self.receipts_by_context_id)+1:06d}",
            receipt_reference=reference,
            receipt_reference_hash=hmac_sha256_prefixed(self.receipt_reference_pepper, reference),
            merchant_display_label="PayRegister merchant",
            store_display_label="PayRegister store",
            terminal_display_label="PayRegister terminal" if context.terminal_hash else None,
            order_reference_hash=context.order_reference_hash,
            amount_msat=amount,
            invoice_hash_fingerprint=context.invoice_hash,
            payment_hash_fingerprint=context.payment_hash,
            settled_at=context.settled_at,
            metadata_hash=context.metadata_hash,
            payment_proof_fingerprint=proof_fingerprint,
            audit_event_hash=audit_hash,
            refund_status="not_refunded",
        )
        self.proofs_by_context_id[context_id] = proof
        self.receipts_by_context_id[context_id] = receipt
        updated = replace(context, receipt_id=receipt.receipt_id, receipt_reference_hash=receipt.receipt_reference_hash, payment_proof_hash=proof_fingerprint)
        self.endpoint_service.repository.save_context(updated)
        return proof, receipt
