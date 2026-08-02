from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from bitcoin_bastion_sdk.wallet_auth.intents import BastionAuthIntent
from bitcoin_bastion_sdk.redaction import redact_secret

PROOF_STRENGTH = {
    "legacy_message_signature": "compatibility",
    "bip322": "standard",
    "hardware_wallet": "high_assurance",
    "air_gapped": "high_assurance",
    "multisig_quorum": "sovereign",
}


@dataclass(frozen=True, slots=True)
class WalletProof:
    proof_type: str
    signature: str = field(repr=False)
    wallet_identifier: str = field(repr=False)

    @property
    def expected_strength(self) -> str:
        try:
            return PROOF_STRENGTH[self.proof_type]
        except KeyError as exc:
            raise ValueError("Unsupported wallet proof type") from exc

    def __repr__(self) -> str:
        return f"WalletProof(proof_type={self.proof_type!r}, signature={redact_secret(self.signature)!r})"


class WalletProofSigner(Protocol):
    def sign_bastion_intent(self, intent: BastionAuthIntent) -> WalletProof: ...
