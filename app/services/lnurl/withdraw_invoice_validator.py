"""Destination invoice validation for LNURL-withdraw payouts."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.lnurl.withdraw_risk import LNURLWithdrawRiskDecision
from app.services.access.crypto.hashing import hmac_sha256_prefixed, sha256_prefixed
from app.services.lnurl.bolt11 import Bolt11InvoiceDecoder, ProjectBolt11Decoder


@dataclass(frozen=True)
class LNURLWithdrawInvoiceValidationRequest:
    invoice: str
    expected_network: str
    expected_amount_msat: int
    server_pepper: str = "test-pepper"
    allow_zero_amount: bool = False
    min_remaining_ttl_seconds: int = 120
    used_invoice_hashes: frozenset[str] = field(default_factory=frozenset)
    used_payment_hash_hashes: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class LNURLWithdrawInvoiceValidationResult:
    allowed: bool
    decision: LNURLWithdrawRiskDecision
    reason_code: str
    invoice_hash: str | None = None
    payment_hash_hash: str | None = None
    amount_msat: int | None = None
    network: str | None = None
    expires_at: datetime | None = None


class LNURLWithdrawInvoiceValidator:
    def __init__(self, decoder: Bolt11InvoiceDecoder | None = None) -> None:
        self.decoder = decoder or ProjectBolt11Decoder()

    def validate(self, request: LNURLWithdrawInvoiceValidationRequest) -> LNURLWithdrawInvoiceValidationResult:
        if not request.invoice or any(ord(char) < 32 for char in request.invoice) or len(request.invoice) > 5000:
            return self._reject("invoice_invalid")
        try:
            decoded = self.decoder.decode(request.invoice)
        except Exception:
            return self._reject("invoice_invalid")
        invoice_hash = sha256_prefixed(request.invoice.lower())
        payment_hash_hash = hmac_sha256_prefixed(request.server_pepper, decoded.payment_hash)
        if invoice_hash in request.used_invoice_hashes or payment_hash_hash in request.used_payment_hash_hashes:
            return self._reject("invoice_duplicate", invoice_hash, payment_hash_hash, decoded.amount_msat, decoded.network, decoded.expires_at)
        if decoded.network != request.expected_network:
            return self._reject("invoice_network_mismatch", invoice_hash, payment_hash_hash, decoded.amount_msat, decoded.network, decoded.expires_at)
        if decoded.amount_msat is None:
            return self._reject("invoice_amount_missing", invoice_hash, payment_hash_hash, None, decoded.network, decoded.expires_at)
        if decoded.amount_msat == 0 and not request.allow_zero_amount:
            return self._reject("zero_amount_invoice_rejected", invoice_hash, payment_hash_hash, decoded.amount_msat, decoded.network, decoded.expires_at)
        if decoded.amount_msat != request.expected_amount_msat:
            return self._reject("invoice_amount_mismatch", invoice_hash, payment_hash_hash, decoded.amount_msat, decoded.network, decoded.expires_at)
        now = datetime.now(UTC)
        if decoded.expires_at <= now:
            return self._reject("invoice_expired", invoice_hash, payment_hash_hash, decoded.amount_msat, decoded.network, decoded.expires_at)
        remaining = int((decoded.expires_at - now).total_seconds())
        if remaining < request.min_remaining_ttl_seconds:
            return self._reject("invoice_ttl_too_short", invoice_hash, payment_hash_hash, decoded.amount_msat, decoded.network, decoded.expires_at)
        return LNURLWithdrawInvoiceValidationResult(True, LNURLWithdrawRiskDecision.ALLOW, "invoice_valid", invoice_hash, payment_hash_hash, decoded.amount_msat, decoded.network, decoded.expires_at)

    @staticmethod
    def _reject(reason: str, invoice_hash: str | None = None, payment_hash_hash: str | None = None, amount_msat: int | None = None, network: str | None = None, expires_at: datetime | None = None) -> LNURLWithdrawInvoiceValidationResult:
        return LNURLWithdrawInvoiceValidationResult(False, LNURLWithdrawRiskDecision.DESTINATION_REJECTED, reason, invoice_hash, payment_hash_hash, amount_msat, network, expires_at)
