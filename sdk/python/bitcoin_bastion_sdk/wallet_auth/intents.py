from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

SAFETY_WARNING = (
    "This signature does not authorize a Bitcoin transaction. This signature only proves "
    "wallet control for Bastion access."
)


@dataclass(frozen=True, slots=True)
class BastionAuthIntent:
    version: int
    domain: str
    action: str
    network: str
    challenge_id: str
    canonical_intent: str
    intent_hash: str
    expires_at: datetime
    device_key_fingerprint: str | None = None
    policy_hash: str | None = None
    risk_level: str = "low"

    @property
    def signable_intent(self) -> str:
        if not self.canonical_intent.startswith("{"):
            raise ValueError("Bastion intent must be structured canonical JSON")
        return self.canonical_intent

    @property
    def safety_warning(self) -> str:
        return SAFETY_WARNING
