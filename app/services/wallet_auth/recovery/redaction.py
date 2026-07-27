from collections.abc import Mapping
from typing import Any

from app.services.wallet_auth.recovery.errors import RecoveryCapsuleError

SAFETY_WARNING = "Bastion never asks for your Bitcoin wallet seed, mnemonic, or private key."
_FORBIDDEN = (
    "seed",
    "mnemonic",
    "seed_phrase",
    "wallet_seed",
    "bitcoin_seed",
    "private_key",
    "xprv",
    "wif",
    "signing_key",
    "recovery_phrase",
    "session_token",
    "access_pass",
    "raw_k1",
    "signature",
)


def reject_forbidden_recovery_input(payload: Mapping[str, Any]) -> None:
    def walk(value: Any) -> bool:
        if isinstance(value, Mapping):
            return any(
                (
                    not str(key).lower().endswith("_signature_metadata")
                    and any(part in str(key).lower() for part in _FORBIDDEN)
                )
                or walk(child)
                for key, child in value.items()
            )
        if isinstance(value, (list, tuple)):
            return any(walk(item) for item in value)
        if isinstance(value, str):
            lowered = value.strip().lower()
            return lowered.startswith(("xprv", "tprv")) or len(lowered.split()) in {
                12,
                15,
                18,
                21,
                24,
            }
        return False

    if walk(payload):
        raise RecoveryCapsuleError(SAFETY_WARNING)


def safe_recovery_metadata(metadata: Mapping[str, Any]) -> dict[str, Any]:
    reject_forbidden_recovery_input(metadata)
    return {str(key): value for key, value in metadata.items()}
