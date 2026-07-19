"""LNURL-withdraw callback verifier.

This module validates the wallet callback (k1 + BOLT-11 invoice) for a
previously issued LNURL-withdraw request. It stores a protected payout
instruction and creates policy handoff/audit evidence, but it never pays the
invoice or treats possession of k1 as payout authorization.
"""
from __future__ import annotations

import re
import threading
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Protocol
from urllib.parse import urlparse

from app.services.access.crypto.hashing import hash_canonical_json_prefixed, hmac_sha256_prefixed, safe_hash_for_log, sha256_prefixed
from app.services.lnurl.bolt11 import Bolt11InvoiceDecoder, DecodedBolt11Invoice, ProjectBolt11Decoder
from app.services.lnurl.errors import VerifyResponseMalformedError
from app.services.lnurl.k1_registry import LNURLK1Purpose
from app.services.lnurl.repositories.withdraw_requests import (
    LNURLWithdrawRequestRecord,
    LNURLWithdrawRequestStatus,
    transition_withdraw_request,
)
from app.services.lnurl.withdraw_request_service import LNURLWithdrawRequestService

_WITHDRAW_ID_RE = re.compile(r"^wdr_[A-Za-z0-9_-]{12,80}$")
_K1_RE = re.compile(r"^[0-9a-f]{64}$")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
_GENERIC_ERROR = "Withdrawal request is invalid, expired, or unavailable."
_INVOICE_ERROR = "Withdrawal invoice is invalid or unavailable."


class LNURLWithdrawCallbackReason(StrEnum):
    WITHDRAW_NOT_FOUND = "withdraw_not_found"
    WITHDRAW_UNAVAILABLE = "withdraw_unavailable"
    WITHDRAW_EXPIRED = "withdraw_expired"
    WITHDRAW_REVOKED = "withdraw_revoked"
    WITHDRAW_INVALID_STATE = "withdraw_invalid_state"
    K1_INVALID_FORMAT = "k1_invalid_format"
    K1_MISMATCH = "k1_mismatch"
    K1_EXPIRED = "k1_expired"
    K1_REUSED = "k1_reused"
    CALLBACK_CONCURRENCY_CONFLICT = "callback_concurrency_conflict"
    INVOICE_MISSING = "invoice_missing"
    INVOICE_TOO_LARGE = "invoice_too_large"
    INVOICE_DECODE_FAILED = "invoice_decode_failed"
    INVOICE_NETWORK_MISMATCH = "invoice_network_mismatch"
    INVOICE_AMOUNT_MISSING = "invoice_amount_missing"
    INVOICE_AMOUNT_BELOW_MINIMUM = "invoice_amount_below_minimum"
    INVOICE_AMOUNT_ABOVE_MAXIMUM = "invoice_amount_above_maximum"
    INVOICE_AMOUNT_NOT_AUTHORIZED = "invoice_amount_not_authorized"
    INVOICE_EXPIRED = "invoice_expired"
    INVOICE_TTL_TOO_SHORT = "invoice_ttl_too_short"
    INVOICE_DUPLICATE = "invoice_duplicate"
    PAYMENT_HASH_DUPLICATE = "payment_hash_duplicate"
    SENSITIVE_INVOICE_STORE_UNAVAILABLE = "sensitive_invoice_store_unavailable"
    POLICY_HANDOFF_FAILED = "policy_handoff_failed"
    INTERNAL_VERIFICATION_ERROR = "internal_verification_error"
    ACCEPTED = "accepted"
    DUPLICATE_ACCEPTED = "duplicate_callback_accepted"


class LNURLWithdrawCallbackError(ValueError):
    def __init__(self, reason_code: LNURLWithdrawCallbackReason | str, *, public_reason: str = _GENERIC_ERROR) -> None:
        super().__init__(str(reason_code))
        self.reason_code = str(reason_code)
        self.public_reason = public_reason


@dataclass(frozen=True, slots=True)
class LNURLWithdrawCallbackVerifierConfig:
    max_invoice_length: int = 4096
    min_invoice_remaining_ttl_seconds: int = 120
    server_pepper: str = "dev-lnurl-withdraw-pepper-change-me"
    allow_amountless_invoices: bool = False
    require_protected_invoice_store: bool = True
    invoice_key_id: str = "lnurl-withdraw-invoice-store-test-key"


@dataclass(frozen=True, slots=True)
class ProtectedInvoiceRecord:
    invoice_store_reference: str
    invoice_hash: str
    invoice_key_id: str


class SensitiveInvoiceStore(Protocol):
    def store(self, *, invoice: str, invoice_hash: str, request_hash: str) -> ProtectedInvoiceRecord: ...


class UnavailableSensitiveInvoiceStore:
    def store(self, *, invoice: str, invoice_hash: str, request_hash: str) -> ProtectedInvoiceRecord:
        raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.SENSITIVE_INVOICE_STORE_UNAVAILABLE)


class InMemorySensitiveInvoiceStore:
    """Test/local adapter. Production deployments should replace this with encrypted storage."""

    def __init__(self, *, key_id: str = "test-only-lnurl-withdraw-invoice-key") -> None:
        self.key_id = key_id
        self.records: dict[str, str] = {}
        self._lock = threading.RLock()

    def store(self, *, invoice: str, invoice_hash: str, request_hash: str) -> ProtectedInvoiceRecord:
        reference = hash_canonical_json_prefixed({"invoice_hash": invoice_hash, "request_hash": request_hash})
        with self._lock:
            self.records[reference] = invoice
        return ProtectedInvoiceRecord(reference, invoice_hash, self.key_id)


@dataclass(frozen=True, slots=True)
class LNURLWithdrawCallbackVerificationResult:
    accepted: bool
    withdraw_public_id: str
    status: str
    invoice_hash: str | None
    payment_hash_commitment: str | None
    amount_msat: int | None
    network: str | None
    invoice_expires_at: datetime | None
    verification_reason_code: str
    policy_evaluation_required: bool
    audit_event_hash: str | None = None
    public_reason: str | None = None

    def lnurl_response(self) -> dict[str, str]:
        if self.accepted:
            return {"status": "OK"}
        return {"status": "ERROR", "reason": self.public_reason or _GENERIC_ERROR}


class LNURLWithdrawCallbackVerifier:
    def __init__(
        self,
        *,
        request_service: LNURLWithdrawRequestService,
        decoder: Bolt11InvoiceDecoder | None = None,
        invoice_store: SensitiveInvoiceStore | None = None,
        config: LNURLWithdrawCallbackVerifierConfig | None = None,
    ) -> None:
        self.request_service = request_service
        self.decoder = decoder or ProjectBolt11Decoder()
        self.config = config or LNURLWithdrawCallbackVerifierConfig(server_pepper=request_service.config.server_pepper)
        self.invoice_store = invoice_store or (UnavailableSensitiveInvoiceStore() if self.config.require_protected_invoice_store else InMemorySensitiveInvoiceStore(key_id=self.config.invoice_key_id))
        self._lock = threading.RLock()

    async def verify_callback(self, *, withdraw_id: str, k1: str, pr: str) -> LNURLWithdrawCallbackVerificationResult:
        try:
            return self._verify_callback_sync(withdraw_id=withdraw_id, k1=k1, pr=pr)
        except LNURLWithdrawCallbackError as exc:
            self._audit("lnurl_withdraw_callback_rejected", {"withdraw_request_hash": _safe_withdraw_hash(withdraw_id), "reason_code": exc.reason_code})
            return LNURLWithdrawCallbackVerificationResult(False, _safe_public_id(withdraw_id), "rejected", None, None, None, None, None, exc.reason_code, False, public_reason=exc.public_reason)
        except Exception:  # noqa: BLE001 - fail closed and keep protocol response generic
            self._audit("lnurl_withdraw_callback_rejected", {"withdraw_request_hash": _safe_withdraw_hash(withdraw_id), "reason_code": LNURLWithdrawCallbackReason.INTERNAL_VERIFICATION_ERROR.value})
            return LNURLWithdrawCallbackVerificationResult(False, _safe_public_id(withdraw_id), "rejected", None, None, None, None, None, LNURLWithdrawCallbackReason.INTERNAL_VERIFICATION_ERROR.value, False, public_reason=_GENERIC_ERROR)

    def _verify_callback_sync(self, *, withdraw_id: str, k1: str, pr: str) -> LNURLWithdrawCallbackVerificationResult:
        self._validate_public_inputs(withdraw_id=withdraw_id, k1=k1, pr=pr)
        decoded = self._decode_invoice(pr)
        invoice_hash = sha256_prefixed(pr)
        payment_hash_commitment = hmac_sha256_prefixed(self.config.server_pepper, decoded.payment_hash)
        with self._lock:
            record = self.request_service.get_request_for_callback_reference(withdraw_id)
            if record is None:
                raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.WITHDRAW_NOT_FOUND)
            self._audit("lnurl_withdraw_callback_received", self._audit_payload(record, reason_code="received"))
            if record.status == LNURLWithdrawRequestStatus.INVOICE_RECEIVED:
                return self._handle_idempotent_retry(record, k1, invoice_hash, payment_hash_commitment)
            self._validate_record_available(record)
            self._validate_invoice(decoded, record)
            self._reject_duplicate_invoice(record, invoice_hash, payment_hash_commitment)
            self._consume_k1(record, k1)
            protected = self.invoice_store.store(invoice=pr, invoice_hash=invoice_hash, request_hash=record.withdraw_request_reference_hash)
            now = datetime.now(UTC)
            updated = transition_withdraw_request(record, LNURLWithdrawRequestStatus.INVOICE_RECEIVED, now=now)
            handoff_id = hash_canonical_json_prefixed({"withdraw_request_hash": record.withdraw_request_reference_hash, "invoice_hash": invoice_hash, "amount_msat": decoded.amount_msat, "network": _normalize_network(decoded.network)})
            updated = replace(
                updated,
                callback_received_at=now,
                invoice_hash=invoice_hash,
                payment_hash_hash=payment_hash_commitment,
                invoice_amount_msat=decoded.amount_msat,
                invoice_network=_normalize_network(decoded.network),
                invoice_created_at=decoded.timestamp,
                invoice_expires_at=decoded.expires_at,
                invoice_store_reference=protected.invoice_store_reference,
                invoice_key_id=protected.invoice_key_id,
                policy_handoff_id=handoff_id,
                callback_attempt_count=record.callback_attempt_count + 1,
                callback_last_failure_code=None,
                metadata_json={**(record.metadata_json or {}), "policy_handoff": "created", "invoice_hash": invoice_hash},
            )
            saved = self.request_service.repository.update(updated)
            accepted_hash = self._audit("lnurl_withdraw_callback_accepted", self._audit_payload(saved, reason_code="accepted", invoice_hash=invoice_hash, amount_msat=decoded.amount_msat, submitted_network=_normalize_network(decoded.network)))
            self._audit("lnurl_withdraw_policy_handoff_created", self._audit_payload(saved, reason_code="policy_handoff_created", invoice_hash=invoice_hash, amount_msat=decoded.amount_msat))
            return LNURLWithdrawCallbackVerificationResult(True, saved.opaque_request_id, saved.status.value, invoice_hash, payment_hash_commitment, decoded.amount_msat, _normalize_network(decoded.network), decoded.expires_at, LNURLWithdrawCallbackReason.ACCEPTED.value, True, accepted_hash)

    def _validate_public_inputs(self, *, withdraw_id: str, k1: str, pr: str) -> None:
        if not _WITHDRAW_ID_RE.fullmatch(withdraw_id or ""):
            raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.WITHDRAW_UNAVAILABLE)
        if not _K1_RE.fullmatch(k1 or ""):
            raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.K1_INVALID_FORMAT)
        if not pr:
            raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.INVOICE_MISSING, public_reason=_INVOICE_ERROR)
        if len(pr) > self.config.max_invoice_length:
            raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.INVOICE_TOO_LARGE, public_reason=_INVOICE_ERROR)
        if _CONTROL_RE.search(pr):
            raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.INVOICE_DECODE_FAILED, public_reason=_INVOICE_ERROR)

    def _decode_invoice(self, pr: str) -> DecodedBolt11Invoice:
        if not (pr.lower().startswith(("lnbc", "lntb", "lntbs", "lnbcrt")) or pr.startswith("testbolt11:")):
            raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.INVOICE_DECODE_FAILED, public_reason=_INVOICE_ERROR)
        try:
            decoded = self.decoder.decode(pr)
        except (VerifyResponseMalformedError, Exception) as exc:  # noqa: BLE001
            raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.INVOICE_DECODE_FAILED, public_reason=_INVOICE_ERROR) from exc
        if not decoded.payment_hash:
            raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.INVOICE_DECODE_FAILED, public_reason=_INVOICE_ERROR)
        return decoded

    def _validate_record_available(self, record: LNURLWithdrawRequestRecord) -> None:
        if record.status == LNURLWithdrawRequestStatus.REVOKED:
            raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.WITHDRAW_REVOKED)
        if record.status == LNURLWithdrawRequestStatus.EXPIRED or record.expires_at <= datetime.now(UTC):
            self._audit("lnurl_withdraw_k1_expired", self._audit_payload(record, reason_code="withdraw_expired"))
            raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.WITHDRAW_EXPIRED)
        if record.status != LNURLWithdrawRequestStatus.LNURL_ISSUED:
            raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.WITHDRAW_INVALID_STATE)

    def _validate_invoice(self, decoded: DecodedBolt11Invoice, record: LNURLWithdrawRequestRecord) -> None:
        submitted_network = _normalize_network(decoded.network)
        if submitted_network != _normalize_network(record.network):
            self._audit("lnurl_withdraw_invoice_network_mismatch", self._audit_payload(record, reason_code="network_mismatch", submitted_network=submitted_network))
            raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.INVOICE_NETWORK_MISMATCH, public_reason=_INVOICE_ERROR)
        if decoded.amount_msat is None:
            if not self.config.allow_amountless_invoices:
                raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.INVOICE_AMOUNT_MISSING, public_reason=_INVOICE_ERROR)
        elif decoded.amount_msat <= 0:
            raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.INVOICE_AMOUNT_MISSING, public_reason=_INVOICE_ERROR)
        amount = decoded.amount_msat
        if amount is None:
            return
        if amount < record.min_withdrawable_msat:
            raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.INVOICE_AMOUNT_BELOW_MINIMUM, public_reason=_INVOICE_ERROR)
        if amount > record.max_withdrawable_msat:
            raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.INVOICE_AMOUNT_ABOVE_MAXIMUM, public_reason=_INVOICE_ERROR)
        if record.min_withdrawable_msat == record.max_withdrawable_msat and amount != record.max_withdrawable_msat:
            raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.INVOICE_AMOUNT_NOT_AUTHORIZED, public_reason=_INVOICE_ERROR)
        now = datetime.now(UTC)
        if decoded.expires_at <= now:
            raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.INVOICE_EXPIRED, public_reason=_INVOICE_ERROR)
        remaining = int((decoded.expires_at - now).total_seconds())
        if remaining < self.config.min_invoice_remaining_ttl_seconds:
            raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.INVOICE_TTL_TOO_SHORT, public_reason=_INVOICE_ERROR)

    def _reject_duplicate_invoice(self, record: LNURLWithdrawRequestRecord, invoice_hash: str, payment_hash_commitment: str) -> None:
        by_invoice = self.request_service.repository.get_by_invoice_hash(invoice_hash)
        if by_invoice is not None and by_invoice.opaque_request_id != record.opaque_request_id:
            raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.INVOICE_DUPLICATE, public_reason=_INVOICE_ERROR)
        by_payment_hash = self.request_service.repository.get_by_payment_hash_hash(payment_hash_commitment)
        if by_payment_hash is not None and by_payment_hash.opaque_request_id != record.opaque_request_id:
            raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.PAYMENT_HASH_DUPLICATE, public_reason=_INVOICE_ERROR)

    def _consume_k1(self, record: LNURLWithdrawRequestRecord, k1: str) -> None:
        try:
            self.request_service.k1_registry.consume_k1(
                k1,
                expected_purpose=LNURLK1Purpose.LNURL_WITHDRAW.value,
                expected_lnurl_action="lnurl_withdraw_callback",
                expected_internal_action=record.purpose,
                expected_domain=self._callback_host(),
                expected_policy_hash=record.policy_hash,
                expected_principal_hash=record.principal_reference_hash,
                expected_device_key_fingerprint=record.device_reference_hash,
                expected_session_hash=record.session_reference_hash,
                expected_withdraw_request_hash=record.withdraw_request_reference_hash,
            )
        except Exception as exc:  # noqa: BLE001 - map k1 internals to safe callback reason
            self.request_service.k1_registry.record_k1_failure(k1, "k1_mismatch")
            self._audit("lnurl_withdraw_k1_invalid", self._audit_payload(record, reason_code="k1_mismatch"))
            raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.K1_MISMATCH) from exc

    def _handle_idempotent_retry(self, record: LNURLWithdrawRequestRecord, k1: str, invoice_hash: str, payment_hash_commitment: str) -> LNURLWithdrawCallbackVerificationResult:
        submitted_fingerprint = sha256_prefixed(bytes.fromhex(k1))
        if submitted_fingerprint != record.k1_fingerprint:
            raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.K1_REUSED)
        if record.invoice_hash == invoice_hash and record.payment_hash_hash == payment_hash_commitment:
            event_hash = self._audit("lnurl_withdraw_callback_accepted", self._audit_payload(record, reason_code="duplicate_callback_accepted", invoice_hash=invoice_hash, amount_msat=record.invoice_amount_msat))
            return LNURLWithdrawCallbackVerificationResult(True, record.opaque_request_id, record.status.value, record.invoice_hash, record.payment_hash_hash, record.invoice_amount_msat, record.invoice_network, record.invoice_expires_at, LNURLWithdrawCallbackReason.DUPLICATE_ACCEPTED.value, True, event_hash)
        self._audit("lnurl_withdraw_callback_rejected", self._audit_payload(record, reason_code="invoice_substitution", invoice_hash=invoice_hash))
        raise LNURLWithdrawCallbackError(LNURLWithdrawCallbackReason.INVOICE_DUPLICATE, public_reason=_INVOICE_ERROR)

    def _callback_host(self) -> str:
        parsed = urlparse(self.request_service.config.callback_base_url)
        return (parsed.hostname or "").lower()

    def _audit_payload(self, record: LNURLWithdrawRequestRecord, *, reason_code: str, invoice_hash: str | None = None, amount_msat: int | None = None, submitted_network: str | None = None) -> dict[str, Any]:
        return {
            "withdraw_request_hash": record.withdraw_request_reference_hash,
            "principal_hash": safe_hash_for_log(record.principal_reference_hash),
            "actor_type": record.principal_type,
            "amount_msat": amount_msat,
            "invoice_hash": invoice_hash,
            "reason_code": reason_code,
            "request_state": record.status.value,
            "expected_network": _normalize_network(record.network),
            "submitted_network": submitted_network,
            "policy_snapshot_hash": record.policy_hash,
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }

    def _audit(self, event_type: str, payload: dict[str, Any]) -> str:
        return self.request_service.audit_sink.emit(event_type, payload)


def _normalize_network(network: str) -> str:
    value = (network or "").lower()
    return {
        "lnbc": "bitcoin-mainnet",
        "bc": "bitcoin-mainnet",
        "bitcoin": "bitcoin-mainnet",
        "mainnet": "bitcoin-mainnet",
        "bitcoin-mainnet": "bitcoin-mainnet",
        "lntb": "bitcoin-testnet",
        "tb": "bitcoin-testnet",
        "testnet": "bitcoin-testnet",
        "bitcoin-testnet": "bitcoin-testnet",
        "lntbs": "bitcoin-signet",
        "signet": "bitcoin-signet",
        "bitcoin-signet": "bitcoin-signet",
        "lnbcrt": "bitcoin-regtest",
        "regtest": "bitcoin-regtest",
        "bitcoin-regtest": "bitcoin-regtest",
    }.get(value, value)


def _safe_withdraw_hash(withdraw_id: str) -> str:
    return safe_hash_for_log(withdraw_id or "unknown")


def _safe_public_id(withdraw_id: str) -> str:
    return withdraw_id if _WITHDRAW_ID_RE.fullmatch(withdraw_id or "") else "wdr_invalid"


__all__ = [
    "InMemorySensitiveInvoiceStore",
    "LNURLWithdrawCallbackError",
    "LNURLWithdrawCallbackReason",
    "LNURLWithdrawCallbackVerificationResult",
    "LNURLWithdrawCallbackVerifier",
    "LNURLWithdrawCallbackVerifierConfig",
    "ProtectedInvoiceRecord",
    "SensitiveInvoiceStore",
    "UnavailableSensitiveInvoiceStore",
]
