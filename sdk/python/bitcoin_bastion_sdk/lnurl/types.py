from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from bitcoin_bastion_sdk.redaction import redact_secret


class LNURLPaymentState(str, Enum):
    CREATED = "created"
    INVOICE_ISSUED = "invoice_issued"
    PENDING = "pending"
    SETTLED = "settled"
    VERIFIED = "verified"
    EXPIRED = "expired"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class LNURLAuthChallenge:
    challenge_id: str
    lnurl: str
    action: str
    auth_domain: str
    expires_at: datetime
    k1: str | None = field(default=None, repr=False)

    def __repr__(self) -> str:
        return (
            f"LNURLAuthChallenge(challenge_id={self.challenge_id!r}, action={self.action!r}, "
            f"auth_domain={self.auth_domain!r}, k1={redact_secret(self.k1)!r})"
        )


@dataclass(frozen=True, slots=True)
class LNURLPayment:
    payment_id: str
    state: LNURLPaymentState
    lnurl: str | None = None
    min_sendable_msat: int | None = None
    max_sendable_msat: int | None = None
    entitlement_active: bool = False

    @property
    def settled(self) -> bool:
        return self.state in {LNURLPaymentState.SETTLED, LNURLPaymentState.VERIFIED}
