"""PayRegister receipt packets bound to cashier/shift context."""
from __future__ import annotations

import secrets
from dataclasses import dataclass, replace
from datetime import datetime

from app.domain.payregister_lnurl.contexts import PayRegisterCanonicalContext, PayRegisterReceiptPacket
from app.domain.payregister_lnurl.errors import PayRegisterIntegrityError
from app.domain.payregister_lnurl.statuses import PayRegisterReceiptStatus
from app.services.access.crypto.hashing import hmac_sha256_prefixed
from app.services.payregister.context_integrity import compute_context_hash


@dataclass(frozen=True, slots=True)
class PayRegisterReceiptInput:
    context: PayRegisterCanonicalContext
    payment_proof_hash: str
    lnurl_payment_request_hash: str
    settled_at: datetime
    audit_event_hash: str


class PayRegisterReceiptService:
    def __init__(self, *, pepper: str = "dev-payregister-receipt-pepper-change-me") -> None:
        self.pepper = pepper
        self.receipts_by_payment_proof_hash: dict[str, PayRegisterReceiptPacket] = {}

    def issue_receipt(self, request: PayRegisterReceiptInput) -> PayRegisterReceiptPacket:
        existing = self.receipts_by_payment_proof_hash.get(request.payment_proof_hash)
        if existing:
            return existing
        if not request.payment_proof_hash.startswith("sha256:") or not request.lnurl_payment_request_hash.startswith("sha256:"):
            raise PayRegisterIntegrityError("Receipt requires hashed proof and request references")
        receipt_id = f"rcpt_{secrets.token_urlsafe(18)}"
        receipt_hash = hmac_sha256_prefixed(self.pepper, f"{receipt_id}:{compute_context_hash(request.context)}")
        packet = PayRegisterReceiptPacket(
            packet_type="bastion_payregister_receipt",
            version=1,
            receipt_id=receipt_hash,
            workspace_hash=request.context.workspace_hash,
            store_hash=request.context.store_hash,
            terminal_hash=request.context.terminal_hash,
            shift_hash=request.context.shift_hash,
            order_hash=request.context.order_hash,
            merchant_invoice_hash=request.context.merchant_invoice_hash,
            lnurl_payment_request_hash=request.lnurl_payment_request_hash,
            payment_proof_hash=request.payment_proof_hash,
            amount_msat=request.context.amount_msat,
            settled_at=request.settled_at,
            metadata_hash=request.context.metadata_hash,
            audit_event_hash=request.audit_event_hash,
            status=PayRegisterReceiptStatus.ISSUED,
        )
        self.receipts_by_payment_proof_hash[request.payment_proof_hash] = packet
        return packet

    def void_receipt(self, payment_proof_hash: str) -> PayRegisterReceiptPacket:
        receipt = self.receipts_by_payment_proof_hash[payment_proof_hash]
        voided = replace(receipt, status=PayRegisterReceiptStatus.VOIDED)
        self.receipts_by_payment_proof_hash[payment_proof_hash] = voided
        return voided
