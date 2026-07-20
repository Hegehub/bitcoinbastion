"""Transaction-safe in-memory refund balance accounting for LNURL-withdraw."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import RLock
from uuid import uuid4


class RefundAccountingError(ValueError):
    pass


@dataclass
class RefundPaymentState:
    original_payment_hash: str
    original_amount_msat: int
    settled: bool = True
    confirmed_refunded_amount_msat: int = 0
    reserved_refund_amount_msat: int = 0
    max_refund_percent: int = 100


@dataclass
class RefundReservation:
    reservation_id: str
    original_payment_hash: str
    withdraw_request_id: str
    reserved_amount_msat: int
    status: str
    expires_at: datetime
    created_at: datetime
    released_at: datetime | None = None


class InMemoryRefundAccountingService:
    def __init__(self) -> None:
        self._lock = RLock()
        self._payments: dict[str, RefundPaymentState] = {}
        self._reservations: dict[str, RefundReservation] = {}

    def put_payment(self, payment: RefundPaymentState) -> None:
        if payment.original_amount_msat <= 0:
            raise RefundAccountingError("original_amount_invalid")
        with self._lock:
            self._payments[payment.original_payment_hash] = payment

    def remaining_refundable_amount_msat(self, original_payment_hash: str) -> int:
        with self._lock:
            payment = self._require_payment(original_payment_hash)
            refundable_cap = payment.original_amount_msat * payment.max_refund_percent // 100
            return max(0, refundable_cap - payment.confirmed_refunded_amount_msat - payment.reserved_refund_amount_msat)

    def reserve_refund(self, *, original_payment_hash: str, withdraw_request_id: str, amount_msat: int, ttl_seconds: int = 900) -> RefundReservation:
        if amount_msat <= 0:
            raise RefundAccountingError("refund_amount_invalid")
        with self._lock:
            payment = self._require_payment(original_payment_hash)
            if not payment.settled:
                raise RefundAccountingError("original_payment_not_settled")
            existing = next((reservation for reservation in self._reservations.values() if reservation.withdraw_request_id == withdraw_request_id and reservation.status == "reserved"), None)
            if existing is not None:
                return existing
            remaining = self.remaining_refundable_amount_msat(original_payment_hash)
            if amount_msat > remaining:
                raise RefundAccountingError("refund_balance_exceeded")
            now = datetime.now(UTC)
            reservation = RefundReservation(
                reservation_id=f"lnwrr_{uuid4().hex}",
                original_payment_hash=original_payment_hash,
                withdraw_request_id=withdraw_request_id,
                reserved_amount_msat=amount_msat,
                status="reserved",
                created_at=now,
                expires_at=now + timedelta(seconds=ttl_seconds),
            )
            payment.reserved_refund_amount_msat += amount_msat
            self._reservations[reservation.reservation_id] = reservation
            return reservation

    def confirm_refund(self, reservation_id: str) -> RefundReservation:
        with self._lock:
            reservation = self._require_reservation(reservation_id)
            if reservation.status == "confirmed":
                return reservation
            if reservation.status != "reserved":
                raise RefundAccountingError("reservation_not_active")
            payment = self._require_payment(reservation.original_payment_hash)
            payment.reserved_refund_amount_msat -= reservation.reserved_amount_msat
            payment.confirmed_refunded_amount_msat += reservation.reserved_amount_msat
            reservation.status = "confirmed"
            return reservation

    def release_reservation(self, reservation_id: str, *, terminal_failure: bool = True) -> RefundReservation:
        with self._lock:
            reservation = self._require_reservation(reservation_id)
            if reservation.status in {"released", "confirmed"}:
                return reservation
            if not terminal_failure:
                raise RefundAccountingError("ambiguous_payment_retains_reservation")
            payment = self._require_payment(reservation.original_payment_hash)
            payment.reserved_refund_amount_msat -= reservation.reserved_amount_msat
            reservation.status = "released"
            reservation.released_at = datetime.now(UTC)
            return reservation

    def _require_payment(self, original_payment_hash: str) -> RefundPaymentState:
        payment = self._payments.get(original_payment_hash)
        if payment is None:
            raise RefundAccountingError("original_payment_missing")
        return payment

    def _require_reservation(self, reservation_id: str) -> RefundReservation:
        reservation = self._reservations.get(reservation_id)
        if reservation is None:
            raise RefundAccountingError("reservation_missing")
        return reservation
