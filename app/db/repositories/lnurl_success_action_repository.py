"""Repository boundary for LNURL successAction activation records.

The in-memory implementation is used by tests and local composition. Production
SQLAlchemy wiring can implement the same protocol without changing services.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from typing import Any, Protocol

from app.domain.lnurl.success_actions import LNURLActivationPurpose, LNURLActivationStatus, LNURLSuccessActionType


@dataclass(frozen=True, slots=True)
class LNURLSuccessActionRecord:
    activation_id: str
    action_type: LNURLSuccessActionType
    purpose: LNURLActivationPurpose
    activation_reference_hash: str
    payment_request_id: str
    callback_origin_hash: str
    callback_host: str
    safe_target_path: str
    status: LNURLActivationStatus
    expires_at: datetime
    payment_proof_id: str | None = None
    entitlement_id: str | None = None
    wallet_principal_hash: str | None = None
    lightning_principal_hash: str | None = None
    merchant_context_hash: str | None = None
    payregister_context_hash: str | None = None
    message_template_code: str | None = None
    description_template_code: str | None = None
    opened_at: datetime | None = None
    completed_at: datetime | None = None
    revoked_at: datetime | None = None
    refunded_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata_json: dict[str, Any] = field(default_factory=dict)


class LNURLSuccessActionRepository(Protocol):
    async def create_success_action(self, record: LNURLSuccessActionRecord) -> LNURLSuccessActionRecord: ...
    async def get_by_activation_reference_hash(self, activation_reference_hash: str) -> LNURLSuccessActionRecord | None: ...
    async def get_by_payment_request_id(self, payment_request_id: str) -> list[LNURLSuccessActionRecord]: ...
    async def get_active_for_payment_and_purpose(self, payment_request_id: str, purpose: LNURLActivationPurpose) -> LNURLSuccessActionRecord | None: ...
    async def mark_payment_pending(self, activation_id: str) -> LNURLSuccessActionRecord: ...
    async def mark_payment_settled(self, activation_id: str, payment_proof_id: str | None = None) -> LNURLSuccessActionRecord: ...
    async def mark_entitlement_pending(self, activation_id: str) -> LNURLSuccessActionRecord: ...
    async def mark_ready(self, activation_id: str, entitlement_id: str | None = None) -> LNURLSuccessActionRecord: ...
    async def mark_opened(self, activation_id: str) -> LNURLSuccessActionRecord: ...
    async def mark_completed(self, activation_id: str) -> LNURLSuccessActionRecord: ...
    async def mark_expired(self, activation_id: str) -> LNURLSuccessActionRecord: ...
    async def revoke(self, activation_id: str) -> LNURLSuccessActionRecord: ...
    async def mark_refunded(self, activation_id: str) -> LNURLSuccessActionRecord: ...


class InMemoryLNURLSuccessActionRepository:
    def __init__(self) -> None:
        self._records: dict[str, LNURLSuccessActionRecord] = {}
        self._by_hash: dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def create_success_action(self, record: LNURLSuccessActionRecord) -> LNURLSuccessActionRecord:
        async with self._lock:
            if record.activation_reference_hash in self._by_hash:
                raise ValueError("duplicate_activation_reference")
            existing = await self._get_active_unlocked(record.payment_request_id, record.purpose)
            if existing is not None:
                return existing
            self._records[record.activation_id] = record
            self._by_hash[record.activation_reference_hash] = record.activation_id
            return record

    async def get_by_activation_reference_hash(self, activation_reference_hash: str) -> LNURLSuccessActionRecord | None:
        async with self._lock:
            activation_id = self._by_hash.get(activation_reference_hash)
            return self._records.get(activation_id) if activation_id else None

    async def get_by_payment_request_id(self, payment_request_id: str) -> list[LNURLSuccessActionRecord]:
        async with self._lock:
            return [record for record in self._records.values() if record.payment_request_id == payment_request_id]

    async def get_active_for_payment_and_purpose(self, payment_request_id: str, purpose: LNURLActivationPurpose) -> LNURLSuccessActionRecord | None:
        async with self._lock:
            return await self._get_active_unlocked(payment_request_id, purpose)

    async def _get_active_unlocked(self, payment_request_id: str, purpose: LNURLActivationPurpose) -> LNURLSuccessActionRecord | None:
        terminal = {LNURLActivationStatus.COMPLETED, LNURLActivationStatus.EXPIRED, LNURLActivationStatus.REVOKED, LNURLActivationStatus.REFUNDED, LNURLActivationStatus.FAILED}
        for record in self._records.values():
            if record.payment_request_id == payment_request_id and record.purpose == purpose and record.status not in terminal:
                return record
        return None

    async def mark_payment_pending(self, activation_id: str) -> LNURLSuccessActionRecord:
        return await self._transition(activation_id, LNURLActivationStatus.PAYMENT_PENDING)

    async def mark_payment_settled(self, activation_id: str, payment_proof_id: str | None = None) -> LNURLSuccessActionRecord:
        return await self._transition(activation_id, LNURLActivationStatus.PAYMENT_SETTLED, payment_proof_id=payment_proof_id)

    async def mark_entitlement_pending(self, activation_id: str) -> LNURLSuccessActionRecord:
        return await self._transition(activation_id, LNURLActivationStatus.ENTITLEMENT_PENDING)

    async def mark_ready(self, activation_id: str, entitlement_id: str | None = None) -> LNURLSuccessActionRecord:
        return await self._transition(activation_id, LNURLActivationStatus.READY, entitlement_id=entitlement_id)

    async def mark_opened(self, activation_id: str) -> LNURLSuccessActionRecord:
        async with self._lock:
            record = self._require(activation_id)
            if record.opened_at is not None or record.status in {LNURLActivationStatus.COMPLETED, LNURLActivationStatus.EXPIRED, LNURLActivationStatus.REVOKED, LNURLActivationStatus.REFUNDED}:
                return record
            updated = replace(record, status=LNURLActivationStatus.OPENED, opened_at=datetime.now(UTC), updated_at=datetime.now(UTC))
            self._records[activation_id] = updated
            return updated

    async def mark_completed(self, activation_id: str) -> LNURLSuccessActionRecord:
        async with self._lock:
            record = self._require(activation_id)
            if record.status is LNURLActivationStatus.COMPLETED:
                return record
            if record.status in {LNURLActivationStatus.EXPIRED, LNURLActivationStatus.REVOKED, LNURLActivationStatus.REFUNDED}:
                raise ValueError(f"activation_{record.status.value}")
            updated = replace(record, status=LNURLActivationStatus.COMPLETED, completed_at=datetime.now(UTC), updated_at=datetime.now(UTC))
            self._records[activation_id] = updated
            return updated

    async def mark_expired(self, activation_id: str) -> LNURLSuccessActionRecord:
        return await self._transition(activation_id, LNURLActivationStatus.EXPIRED)

    async def revoke(self, activation_id: str) -> LNURLSuccessActionRecord:
        return await self._transition(activation_id, LNURLActivationStatus.REVOKED, revoked_at=datetime.now(UTC))

    async def mark_refunded(self, activation_id: str) -> LNURLSuccessActionRecord:
        return await self._transition(activation_id, LNURLActivationStatus.REFUNDED, refunded_at=datetime.now(UTC))

    async def _transition(self, activation_id: str, status: LNURLActivationStatus, **changes: Any) -> LNURLSuccessActionRecord:
        async with self._lock:
            record = self._require(activation_id)
            if record.status is LNURLActivationStatus.COMPLETED and status is not LNURLActivationStatus.COMPLETED:
                return record
            if record.status in {LNURLActivationStatus.REVOKED, LNURLActivationStatus.REFUNDED, LNURLActivationStatus.EXPIRED} and status is LNURLActivationStatus.COMPLETED:
                raise ValueError(f"activation_{record.status.value}")
            updated = replace(record, status=status, updated_at=datetime.now(UTC), **changes)
            self._records[activation_id] = updated
            return updated

    def _require(self, activation_id: str) -> LNURLSuccessActionRecord:
        record = self._records.get(activation_id)
        if record is None:
            raise KeyError("activation_not_found")
        return record
