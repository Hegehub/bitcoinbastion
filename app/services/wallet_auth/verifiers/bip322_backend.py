"""Replaceable BIP-322 script verification backend boundary.

The default backend is conservative: it never fabricates cryptographic success.
A future backend can plug in a complete Bitcoin script interpreter or narrowly
verified P2WPKH/P2TR implementation without changing verifier orchestration.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from app.domain.wallet_auth.proofs import WalletScriptType


class ScriptVerificationOutcome(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True, slots=True)
class ScriptVerificationResult:
    outcome: ScriptVerificationOutcome
    reason_code: str
    limitations: tuple[str, ...] = ()
    valid_at_time: int | None = None
    valid_at_age: int | None = None


class BIP322ScriptBackend(Protocol):
    @property
    def backend_id(self) -> str: ...

    @property
    def backend_version(self) -> str: ...

    def verify_simple(
        self,
        *,
        to_spend: bytes,
        to_sign: bytes,
        message_challenge: bytes,
        witness_stack: tuple[bytes, ...],
        script_type: WalletScriptType,
    ) -> ScriptVerificationResult: ...

    def verify_full(
        self,
        *,
        to_spend: bytes,
        to_sign: bytes,
        message_challenge: bytes,
        payload: bytes,
        script_type: WalletScriptType,
    ) -> ScriptVerificationResult: ...


@dataclass(frozen=True, slots=True)
class ConservativeBIP322ScriptBackend:
    backend_id: str = "conservative_bip322_backend"
    backend_version: str = "1"

    def verify_simple(
        self,
        *,
        to_spend: bytes,
        to_sign: bytes,
        message_challenge: bytes,
        witness_stack: tuple[bytes, ...],
        script_type: WalletScriptType,
    ) -> ScriptVerificationResult:
        if not witness_stack:
            return ScriptVerificationResult(ScriptVerificationOutcome.INVALID, "empty_witness")
        if script_type == WalletScriptType.P2TR and len(witness_stack) > 1:
            return ScriptVerificationResult(
                ScriptVerificationOutcome.INCONCLUSIVE,
                "unsupported_taproot_script_path",
                ("taproot_script_path_not_implemented",),
            )
        return ScriptVerificationResult(
            ScriptVerificationOutcome.INCONCLUSIVE,
            "script_backend_unavailable",
            ("trusted_script_backend_required", "no_fake_cryptographic_success"),
        )

    def verify_full(
        self,
        *,
        to_spend: bytes,
        to_sign: bytes,
        message_challenge: bytes,
        payload: bytes,
        script_type: WalletScriptType,
    ) -> ScriptVerificationResult:
        return ScriptVerificationResult(
            ScriptVerificationOutcome.INCONCLUSIVE,
            "script_backend_unavailable",
            ("full_variant_requires_trusted_script_backend",),
        )
