"""Velocity counters for LNURL-withdraw risk decisions."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from threading import RLock

from app.domain.lnurl.withdraw_risk import LNURLWithdrawRiskDecision


@dataclass(frozen=True)
class LNURLWithdrawVelocityEvent:
    amount_msat: int
    purpose: str
    network: str
    principal_hash: str | None = None
    business_workspace_hash: str | None = None
    merchant_hash: str | None = None
    payregister_device_hash: str | None = None
    cashier_role_hash: str | None = None
    device_fingerprint: str | None = None
    destination_invoice_hash: str | None = None
    original_payment_hash: str | None = None
    failed: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True)
class LNURLWithdrawVelocityDecision:
    allowed: bool
    decision: LNURLWithdrawRiskDecision
    reason_codes: tuple[str, ...]
    counters: dict[str, int]


class InMemoryLNURLWithdrawVelocityTracker:
    def __init__(self) -> None:
        self._lock = RLock()
        self._events: list[LNURLWithdrawVelocityEvent] = []

    def record(self, event: LNURLWithdrawVelocityEvent) -> None:
        with self._lock:
            self._events.append(event)

    def evaluate(self, event: LNURLWithdrawVelocityEvent, *, max_requests_per_hour: int = 20, max_amount_24h_msat: int = 50_000_000, max_failed_5m: int = 5) -> LNURLWithdrawVelocityDecision:
        now = datetime.now(UTC)
        with self._lock:
            recent_hour = [old for old in self._events if old.created_at >= now - timedelta(hours=1) and self._same_actor(old, event)]
            recent_day = [old for old in self._events if old.created_at >= now - timedelta(days=1) and self._same_actor(old, event)]
            recent_failed = [old for old in self._events if old.created_at >= now - timedelta(minutes=5) and old.failed and self._same_actor(old, event)]
            duplicate_invoice = any(old.destination_invoice_hash and old.destination_invoice_hash == event.destination_invoice_hash for old in self._events)
        counters = {
            "requests_1h": len(recent_hour),
            "amount_24h_msat": sum(old.amount_msat for old in recent_day),
            "failed_5m": len(recent_failed),
        }
        if duplicate_invoice:
            return LNURLWithdrawVelocityDecision(False, LNURLWithdrawRiskDecision.DESTINATION_REJECTED, ("duplicate_destination_invoice",), counters)
        if counters["requests_1h"] >= max_requests_per_hour:
            return LNURLWithdrawVelocityDecision(False, LNURLWithdrawRiskDecision.VELOCITY_EXCEEDED, ("request_velocity_exceeded",), counters)
        if counters["amount_24h_msat"] + event.amount_msat > max_amount_24h_msat:
            return LNURLWithdrawVelocityDecision(False, LNURLWithdrawRiskDecision.VELOCITY_EXCEEDED, ("daily_velocity_amount_exceeded",), counters)
        if counters["failed_5m"] >= max_failed_5m:
            return LNURLWithdrawVelocityDecision(False, LNURLWithdrawRiskDecision.COOLDOWN_REQUIRED, ("failed_callback_cooldown_required",), counters)
        return LNURLWithdrawVelocityDecision(True, LNURLWithdrawRiskDecision.ALLOW, ("velocity_within_limit",), counters)

    @staticmethod
    def _same_actor(left: LNURLWithdrawVelocityEvent, right: LNURLWithdrawVelocityEvent) -> bool:
        return any(
            getattr(left, field_name) and getattr(left, field_name) == getattr(right, field_name)
            for field_name in ("principal_hash", "business_workspace_hash", "merchant_hash", "payregister_device_hash", "device_fingerprint", "original_payment_hash")
        )
