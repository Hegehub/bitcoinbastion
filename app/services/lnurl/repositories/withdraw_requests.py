"""Repositories for LNURL-withdraw request creation.

Raw k1 values are never persisted here. Records store only the k1 registry id,
non-secret k1 fingerprint, and HMAC/SHA-derived request references.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol


class LNURLWithdrawRequestStatus(StrEnum):
    CREATED = "created"
    POLICY_PENDING = "policy_pending"
    POLICY_APPROVED = "policy_approved"
    LNURL_ISSUED = "lnurl_issued"
    INVOICE_RECEIVED = "invoice_received"
    PAYMENT_PENDING = "payment_pending"
    PAID = "paid"
    FAILED = "failed"
    EXPIRED = "expired"
    REVOKED = "revoked"
    CANCELLED = "cancelled"


TERMINAL_WITHDRAW_REQUEST_STATES = frozenset(
    {
        LNURLWithdrawRequestStatus.PAID,
        LNURLWithdrawRequestStatus.FAILED,
        LNURLWithdrawRequestStatus.EXPIRED,
        LNURLWithdrawRequestStatus.REVOKED,
        LNURLWithdrawRequestStatus.CANCELLED,
    }
)

WITHDRAW_REQUEST_TRANSITIONS: dict[LNURLWithdrawRequestStatus, frozenset[LNURLWithdrawRequestStatus]] = {
    LNURLWithdrawRequestStatus.CREATED: frozenset({LNURLWithdrawRequestStatus.POLICY_PENDING, LNURLWithdrawRequestStatus.POLICY_APPROVED, LNURLWithdrawRequestStatus.CANCELLED}),
    LNURLWithdrawRequestStatus.POLICY_PENDING: frozenset({LNURLWithdrawRequestStatus.POLICY_APPROVED, LNURLWithdrawRequestStatus.FAILED, LNURLWithdrawRequestStatus.CANCELLED}),
    LNURLWithdrawRequestStatus.POLICY_APPROVED: frozenset({LNURLWithdrawRequestStatus.LNURL_ISSUED, LNURLWithdrawRequestStatus.CANCELLED}),
    LNURLWithdrawRequestStatus.LNURL_ISSUED: frozenset({LNURLWithdrawRequestStatus.INVOICE_RECEIVED, LNURLWithdrawRequestStatus.EXPIRED, LNURLWithdrawRequestStatus.REVOKED}),
    LNURLWithdrawRequestStatus.INVOICE_RECEIVED: frozenset({LNURLWithdrawRequestStatus.PAYMENT_PENDING, LNURLWithdrawRequestStatus.FAILED, LNURLWithdrawRequestStatus.EXPIRED}),
    LNURLWithdrawRequestStatus.PAYMENT_PENDING: frozenset({LNURLWithdrawRequestStatus.PAID, LNURLWithdrawRequestStatus.FAILED}),
    LNURLWithdrawRequestStatus.PAID: frozenset(),
    LNURLWithdrawRequestStatus.FAILED: frozenset(),
    LNURLWithdrawRequestStatus.EXPIRED: frozenset(),
    LNURLWithdrawRequestStatus.REVOKED: frozenset(),
    LNURLWithdrawRequestStatus.CANCELLED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class LNURLWithdrawRequestRecord:
    opaque_request_id: str
    withdraw_request_reference_hash: str
    purpose: str
    status: LNURLWithdrawRequestStatus
    principal_type: str
    principal_reference_hash: str
    device_reference_hash: str
    session_reference_hash: str
    source_reference_hash: str | None
    policy_decision_reference: str
    policy_hash: str
    k1_registry_id: str
    k1_fingerprint: str
    callback_url_hash: str
    min_withdrawable_msat: int
    max_withdrawable_msat: int
    default_description: str
    network: str
    risk_level: str
    idempotency_key_hash: str
    payload_hash: str
    created_at: datetime
    expires_at: datetime
    issued_at: datetime | None
    revoked_at: datetime | None = None
    cancelled_at: datetime | None = None
    metadata_json: dict[str, Any] | None = None
    callback_received_at: datetime | None = None
    invoice_hash: str | None = None
    payment_hash_hash: str | None = None
    invoice_amount_msat: int | None = None
    invoice_network: str | None = None
    invoice_created_at: datetime | None = None
    invoice_expires_at: datetime | None = None
    invoice_store_reference: str | None = None
    invoice_key_id: str | None = None
    policy_handoff_id: str | None = None
    callback_attempt_count: int = 0
    callback_last_failure_code: str | None = None


class LNURLWithdrawRequestRepository(Protocol):
    def save(self, record: LNURLWithdrawRequestRecord) -> LNURLWithdrawRequestRecord: ...
    def update(self, record: LNURLWithdrawRequestRecord) -> LNURLWithdrawRequestRecord: ...
    def get_by_request_id(self, opaque_request_id: str) -> LNURLWithdrawRequestRecord | None: ...
    def get_by_reference_hash(self, reference_hash: str) -> LNURLWithdrawRequestRecord | None: ...
    def get_by_idempotency_key_hash(self, idempotency_key_hash: str) -> LNURLWithdrawRequestRecord | None: ...
    def active_for_source(self, source_reference_hash: str) -> LNURLWithdrawRequestRecord | None: ...
    def get_by_invoice_hash(self, invoice_hash: str) -> LNURLWithdrawRequestRecord | None: ...
    def get_by_payment_hash_hash(self, payment_hash_hash: str) -> LNURLWithdrawRequestRecord | None: ...


class InMemoryLNURLWithdrawRequestRepository:
    def __init__(self) -> None:
        self._by_id: dict[str, LNURLWithdrawRequestRecord] = {}
        self._by_reference_hash: dict[str, str] = {}
        self._by_idempotency_hash: dict[str, str] = {}
        self._by_invoice_hash: dict[str, str] = {}
        self._by_payment_hash_hash: dict[str, str] = {}
        self._lock = threading.RLock()

    def save(self, record: LNURLWithdrawRequestRecord) -> LNURLWithdrawRequestRecord:
        with self._lock:
            existing_id = self._by_idempotency_hash.get(record.idempotency_key_hash)
            if existing_id is not None:
                return self._by_id[existing_id]
            self._by_id[record.opaque_request_id] = record
            self._by_reference_hash[record.withdraw_request_reference_hash] = record.opaque_request_id
            self._by_idempotency_hash[record.idempotency_key_hash] = record.opaque_request_id
            self._index_invoice_fields(record)
            return record

    def update(self, record: LNURLWithdrawRequestRecord) -> LNURLWithdrawRequestRecord:
        with self._lock:
            self._by_id[record.opaque_request_id] = record
            self._by_reference_hash[record.withdraw_request_reference_hash] = record.opaque_request_id
            self._by_idempotency_hash[record.idempotency_key_hash] = record.opaque_request_id
            self._index_invoice_fields(record)
            return record

    def get_by_request_id(self, opaque_request_id: str) -> LNURLWithdrawRequestRecord | None:
        with self._lock:
            return self._by_id.get(opaque_request_id)

    def get_by_reference_hash(self, reference_hash: str) -> LNURLWithdrawRequestRecord | None:
        with self._lock:
            request_id = self._by_reference_hash.get(reference_hash)
            return self._by_id.get(request_id) if request_id else None

    def get_by_idempotency_key_hash(self, idempotency_key_hash: str) -> LNURLWithdrawRequestRecord | None:
        with self._lock:
            request_id = self._by_idempotency_hash.get(idempotency_key_hash)
            return self._by_id.get(request_id) if request_id else None

    def active_for_source(self, source_reference_hash: str) -> LNURLWithdrawRequestRecord | None:
        with self._lock:
            for record in self._by_id.values():
                if record.source_reference_hash == source_reference_hash and record.status not in TERMINAL_WITHDRAW_REQUEST_STATES:
                    return record
            return None

    def get_by_invoice_hash(self, invoice_hash: str) -> LNURLWithdrawRequestRecord | None:
        with self._lock:
            request_id = self._by_invoice_hash.get(invoice_hash)
            return self._by_id.get(request_id) if request_id else None

    def get_by_payment_hash_hash(self, payment_hash_hash: str) -> LNURLWithdrawRequestRecord | None:
        with self._lock:
            request_id = self._by_payment_hash_hash.get(payment_hash_hash)
            return self._by_id.get(request_id) if request_id else None

    def _index_invoice_fields(self, record: LNURLWithdrawRequestRecord) -> None:
        if record.invoice_hash:
            self._by_invoice_hash[record.invoice_hash] = record.opaque_request_id
        if record.payment_hash_hash:
            self._by_payment_hash_hash[record.payment_hash_hash] = record.opaque_request_id


def can_transition_withdraw_request(current: LNURLWithdrawRequestStatus | str, target: LNURLWithdrawRequestStatus | str) -> bool:
    return LNURLWithdrawRequestStatus(target) in WITHDRAW_REQUEST_TRANSITIONS[LNURLWithdrawRequestStatus(current)]


def transition_withdraw_request(record: LNURLWithdrawRequestRecord, target: LNURLWithdrawRequestStatus, *, now: datetime) -> LNURLWithdrawRequestRecord:
    if not can_transition_withdraw_request(record.status, target):
        raise ValueError("lnurl_withdraw_invalid_state")
    updates: dict[str, Any] = {"status": target}
    if target == LNURLWithdrawRequestStatus.LNURL_ISSUED:
        updates["issued_at"] = now
    if target == LNURLWithdrawRequestStatus.REVOKED:
        updates["revoked_at"] = now
    if target == LNURLWithdrawRequestStatus.CANCELLED:
        updates["cancelled_at"] = now
    return replace(record, **updates)
