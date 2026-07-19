"""Immutable PayRegister LNURL payment and receipt context objects."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.payregister_lnurl.statuses import PayRegisterReceiptStatus


@dataclass(frozen=True, slots=True)
class PayRegisterCanonicalContext:
    context_type: str
    version: int
    context_id: str
    workspace_hash: str
    store_hash: str
    terminal_hash: str
    terminal_device_fingerprint: str
    cashier_role_binding_hash: str
    shift_hash: str
    order_hash: str | None
    merchant_invoice_hash: str | None
    currency: str
    amount_msat: int
    payment_purpose: str
    created_at: datetime
    expires_at: datetime
    policy_hash: str
    metadata_hash: str


@dataclass(frozen=True, slots=True)
class PayRegisterReceiptPacket:
    packet_type: str
    version: int
    receipt_id: str
    workspace_hash: str
    store_hash: str
    terminal_hash: str
    shift_hash: str
    order_hash: str | None
    merchant_invoice_hash: str | None
    lnurl_payment_request_hash: str
    payment_proof_hash: str
    amount_msat: int
    settled_at: datetime
    metadata_hash: str
    audit_event_hash: str
    status: PayRegisterReceiptStatus
