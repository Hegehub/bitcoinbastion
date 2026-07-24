"""Idempotent LNURL-withdraw execution boundary."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock

from app.domain.lnurl.withdraw_risk import LNURLWithdrawFailureCategory, LNURLWithdrawStatus, can_transition
from app.services.access.crypto.hashing import hash_canonical_json_prefixed


class WithdrawExecutionError(RuntimeError):
    pass


@dataclass
class WithdrawExecutionAttempt:
    withdraw_request_id: str
    idempotency_hash: str
    invoice_hash: str
    payment_hash_hash: str
    approved_amount_msat: int
    policy_hash: str
    status: LNURLWithdrawStatus = LNURLWithdrawStatus.PAYMENT_QUEUED
    attempt_number: int = 1
    provider_reference_hash: str | None = None
    failure_category: LNURLWithdrawFailureCategory | None = None
    reconciliation_required: bool = False
    started_at: datetime | None = None
    completed_at: datetime | None = None


class IdempotentLNURLWithdrawExecutor:
    def __init__(self) -> None:
        self._lock = RLock()
        self._attempts: dict[str, WithdrawExecutionAttempt] = {}

    @staticmethod
    def make_idempotency_hash(*, withdraw_request_id: str, invoice_payment_hash: str, approved_amount_msat: int, policy_hash: str) -> str:
        return hash_canonical_json_prefixed(
            {
                "withdraw_request_id": withdraw_request_id,
                "invoice_payment_hash": invoice_payment_hash,
                "approved_amount_msat": approved_amount_msat,
                "policy_hash": policy_hash,
            }
        )

    def enqueue_or_get(self, *, withdraw_request_id: str, invoice_hash: str, payment_hash_hash: str, approved_amount_msat: int, policy_hash: str) -> WithdrawExecutionAttempt:
        key = self.make_idempotency_hash(withdraw_request_id=withdraw_request_id, invoice_payment_hash=payment_hash_hash, approved_amount_msat=approved_amount_msat, policy_hash=policy_hash)
        with self._lock:
            existing = self._attempts.get(key)
            if existing is not None:
                return existing
            attempt = WithdrawExecutionAttempt(withdraw_request_id, key, invoice_hash, payment_hash_hash, approved_amount_msat, policy_hash)
            self._attempts[key] = attempt
            return attempt

    def transition(self, idempotency_hash: str, to_status: LNURLWithdrawStatus, *, failure_category: LNURLWithdrawFailureCategory | None = None, provider_reference_hash: str | None = None) -> WithdrawExecutionAttempt:
        with self._lock:
            attempt = self._attempts[idempotency_hash]
            if not can_transition(attempt.status, to_status):
                raise WithdrawExecutionError("illegal_state_transition")
            attempt.status = to_status
            if to_status == LNURLWithdrawStatus.PAYMENT_IN_FLIGHT:
                attempt.started_at = datetime.now(UTC)
            if to_status in {LNURLWithdrawStatus.PAYMENT_SUCCEEDED, LNURLWithdrawStatus.SETTLEMENT_CONFIRMED, LNURLWithdrawStatus.FAILED_TERMINAL}:
                attempt.completed_at = datetime.now(UTC)
            attempt.failure_category = failure_category
            attempt.provider_reference_hash = provider_reference_hash or attempt.provider_reference_hash
            if failure_category == LNURLWithdrawFailureCategory.PROVIDER_TIMEOUT:
                attempt.reconciliation_required = True
            return attempt

    def provider_timeout(self, idempotency_hash: str) -> WithdrawExecutionAttempt:
        return self.transition(idempotency_hash, LNURLWithdrawStatus.PAYMENT_IN_FLIGHT, failure_category=LNURLWithdrawFailureCategory.PROVIDER_TIMEOUT)
