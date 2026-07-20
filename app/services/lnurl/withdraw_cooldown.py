"""Persisted cooldown decisions for LNURL-withdraw controls."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import RLock

from app.domain.lnurl.withdraw_risk import LNURLWithdrawRiskDecision


@dataclass(frozen=True)
class LNURLWithdrawCooldownRecord:
    subject_hash: str
    reason_code: str
    available_after: datetime
    created_at: datetime


@dataclass(frozen=True)
class LNURLWithdrawCooldownDecision:
    allowed: bool
    decision: LNURLWithdrawRiskDecision
    reason_code: str
    available_after: datetime | None = None


class InMemoryLNURLWithdrawCooldownService:
    def __init__(self) -> None:
        self._lock = RLock()
        self._records: dict[str, LNURLWithdrawCooldownRecord] = {}

    def add_cooldown(self, *, subject_hash: str, reason_code: str, seconds: int) -> LNURLWithdrawCooldownRecord:
        if seconds <= 0:
            raise ValueError("cooldown seconds must be positive")
        now = datetime.now(UTC)
        record = LNURLWithdrawCooldownRecord(subject_hash, reason_code, now + timedelta(seconds=seconds), now)
        with self._lock:
            self._records[subject_hash] = record
        return record

    def evaluate(self, subject_hash: str) -> LNURLWithdrawCooldownDecision:
        now = datetime.now(UTC)
        with self._lock:
            record = self._records.get(subject_hash)
        if record is None or record.available_after <= now:
            return LNURLWithdrawCooldownDecision(True, LNURLWithdrawRiskDecision.ALLOW, "cooldown_clear")
        return LNURLWithdrawCooldownDecision(False, LNURLWithdrawRiskDecision.COOLDOWN_REQUIRED, record.reason_code, record.available_after)
