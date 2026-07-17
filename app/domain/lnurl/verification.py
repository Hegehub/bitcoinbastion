"""LNURL settlement verification domain objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.lnurl.payments import LNURLPaymentVerificationMethod


class LNURLVerifyStatus(StrEnum):
    NOT_REQUESTED = "not_requested"
    NOT_AVAILABLE = "not_requested"
    PENDING = "pending"
    SETTLED = "settled"
    SETTLED_TRUE = "settled"
    UNSETTLED = "unsettled"
    SETTLED_FALSE = "unsettled"
    EXPIRED = "expired"
    INVALID = "invalid"
    PREIMAGE_VERIFIED = "settled"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class LNURLSettlementEvidence:
    status: LNURLVerifyStatus
    verification_method: LNURLPaymentVerificationMethod
    payment_hash_fingerprint: str
    invoice_fingerprint: str
    preimage_fingerprint: str | None = None
    verified_at: datetime | None = None
    provider_reference_hash: str | None = None
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field_name in ("payment_hash_fingerprint", "invoice_fingerprint"):
            if not getattr(self, field_name).startswith(("sha256:", "hmac-sha256:")):
                raise ValueError(f"{field_name}_must_be_fingerprint")
        if self.preimage_fingerprint is not None and not self.preimage_fingerprint.startswith("sha256:"):
            raise ValueError("preimage_fingerprint_must_be_fingerprint")
