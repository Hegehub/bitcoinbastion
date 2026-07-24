"""LNURL-withdraw reconciliation evidence and outcome mapping."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.lnurl.withdraw_risk import LNURLWithdrawFailureCategory, LNURLWithdrawStatus


@dataclass(frozen=True)
class ProviderWithdrawPaymentState:
    found: bool
    settled: bool = False
    failed: bool = False
    amount_msat: int | None = None
    payment_hash_hash: str | None = None
    duplicate_count: int = 0
    provider_reference_hash: str | None = None


@dataclass(frozen=True)
class LocalWithdrawPaymentState:
    withdraw_request_id: str
    status: LNURLWithdrawStatus
    amount_msat: int
    payment_hash_hash: str


@dataclass(frozen=True)
class LNURLWithdrawReconciliationResult:
    outcome: str
    next_status: LNURLWithdrawStatus | None
    failure_category: LNURLWithdrawFailureCategory | None
    audit_payload: dict[str, object]
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class LNURLWithdrawReconciliationService:
    def reconcile(self, local: LocalWithdrawPaymentState, provider: ProviderWithdrawPaymentState) -> LNURLWithdrawReconciliationResult:
        payload = {
            "withdraw_request_hash": local.withdraw_request_id,
            "amount_msat": local.amount_msat,
            "payment_hash_hash": local.payment_hash_hash,
            "provider_reference_hash": provider.provider_reference_hash,
        }
        if provider.duplicate_count > 1:
            return self._result("duplicate_payment_detected", LNURLWithdrawStatus.FAILED_TERMINAL, LNURLWithdrawFailureCategory.RECONCILIATION_MISMATCH, payload)
        if not provider.found:
            return self._result("local_missing_provider_payment", None, LNURLWithdrawFailureCategory.RECONCILIATION_MISMATCH, payload)
        if provider.payment_hash_hash != local.payment_hash_hash:
            return self._result("provider_payment_missing_local_record", LNURLWithdrawStatus.FAILED_TERMINAL, LNURLWithdrawFailureCategory.RECONCILIATION_MISMATCH, payload)
        if provider.amount_msat is not None and provider.amount_msat != local.amount_msat:
            return self._result("amount_mismatch", LNURLWithdrawStatus.FAILED_TERMINAL, LNURLWithdrawFailureCategory.RECONCILIATION_MISMATCH, payload)
        if provider.settled:
            return self._result("matched_settled", LNURLWithdrawStatus.SETTLEMENT_CONFIRMED, None, payload)
        if provider.failed:
            return self._result("matched_failed", LNURLWithdrawStatus.FAILED_RETRYABLE, LNURLWithdrawFailureCategory.PROVIDER_ERROR, payload)
        return self._result("still_pending", LNURLWithdrawStatus.PAYMENT_IN_FLIGHT, None, payload)

    @staticmethod
    def _result(outcome: str, status: LNURLWithdrawStatus | None, failure: LNURLWithdrawFailureCategory | None, payload: dict[str, object]) -> LNURLWithdrawReconciliationResult:
        return LNURLWithdrawReconciliationResult(outcome, status, failure, {**payload, "outcome": outcome})
