"""Typed wallet proof verifier contract for Wallet-first Auth PQ v2.

Security invariants:
- ``verified=True`` means only that the selected adapter verified the submitted
  proof for the submitted structured intent.
- ``verified=True`` does not mean Policy Engine allowed the action, a session
  exists, a subscription entitlement is active, or the wallet owns treasury
  funds.
- Compatibility proofs cannot satisfy critical actions.
- Proofs cannot be verified against a different intent, network, origin,
  action, challenge, nonce commitment, or device binding.
- Unsupported placeholder verifiers never return cryptographic success.
- No verifier accepts Bitcoin seed/private-key material.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from app.domain.wallet_auth.actions import WalletAuthAction
from app.domain.wallet_auth.constants import DEDICATED_AUTH_ADDRESS_WARNING, REQUIRED_SIGNATURE_WARNING
from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.proofs import WalletProofType, WalletScriptType, WalletVerificationStrength
from app.services.wallet_auth.privacy_commitments import (
    compute_address_lookup_hash,
    compute_wallet_proof_hash,
    redact_sensitive_auth_material,
    redact_wallet_identifier,
    reject_forbidden_wallet_secret_input,
)


class WalletProofVerificationReason(StrEnum):
    VERIFIED = "verified"
    INVALID_SIGNATURE = "invalid_signature"
    UNSUPPORTED_PROOF_TYPE = "unsupported_proof_type"
    UNSUPPORTED_NETWORK = "unsupported_network"
    UNSUPPORTED_SCRIPT_TYPE = "unsupported_script_type"
    WALLET_IDENTIFIER_MISMATCH = "wallet_identifier_mismatch"
    INTENT_HASH_MISMATCH = "intent_hash_mismatch"
    ORIGIN_MISMATCH = "origin_mismatch"
    ACTION_MISMATCH = "action_mismatch"
    CHALLENGE_MISMATCH = "challenge_mismatch"
    NONCE_MISMATCH = "nonce_mismatch"
    DEVICE_MISMATCH = "device_mismatch"
    INTENT_EXPIRED = "intent_expired"
    INTENT_NOT_YET_VALID = "intent_not_yet_valid"
    VERIFICATION_STRENGTH_INSUFFICIENT = "verification_strength_insufficient"
    PROOF_REVOKED = "proof_revoked"
    VERIFIER_UNAVAILABLE = "verifier_unavailable"
    MALFORMED_PROOF = "malformed_proof"
    INTERNAL_VERIFICATION_ERROR = "internal_verification_error"
    NOT_IMPLEMENTED = "not_implemented"
    VALID_BIP322_PROOF = "valid_bip322_proof"
    INVALID_BASE64 = "invalid_base64"
    EMPTY_SIGNATURE = "empty_signature"
    UNKNOWN_VARIANT = "unknown_variant"
    PREFIX_REQUIRED = "prefix_required"
    WRONG_VARIANT_PAYLOAD = "wrong_variant_payload"
    INVALID_ADDRESS = "invalid_address"
    WRONG_NETWORK = "wrong_network"
    UNSUPPORTED_SCRIPT = "unsupported_script"
    UNSUPPORTED_TAPROOT_SCRIPT_PATH = "unsupported_taproot_script_path"
    SCRIPT_BACKEND_UNAVAILABLE = "script_backend_unavailable"
    MESSAGE_MISMATCH = "message_mismatch"
    SCRIPT_MISMATCH = "script_mismatch"
    INVALID_TRANSACTION_STRUCTURE = "invalid_transaction_structure"
    FORBIDDEN_SIGHASH = "forbidden_sighash"
    NON_CANONICAL_SIGNATURE = "non_canonical_signature"
    TIMELOCK_NOT_SUPPORTED = "timelock_not_supported"
    PROOF_OF_FUNDS_NOT_ALLOWED_FOR_AUTH = "proof_of_funds_not_allowed_for_auth"
    LEGACY_SIGNATURE_DISABLED = "legacy_signature_disabled"
    LEGACY_SIGNATURE_NOT_ALLOWED_FOR_ACTION = "legacy_signature_not_allowed_for_action"
    LEGACY_SIGNATURE_NOT_ALLOWED_FOR_PLAN = "legacy_signature_not_allowed_for_plan"
    MALFORMED_LEGACY_SIGNATURE = "malformed_legacy_signature"
    INVALID_LEGACY_SIGNATURE = "invalid_legacy_signature"
    UNSUPPORTED_LEGACY_SIGNATURE_FORMAT = "unsupported_legacy_signature_format"
    UNSUPPORTED_ADDRESS_TYPE = "unsupported_address_type"
    WALLET_NETWORK_MISMATCH = "wallet_network_mismatch"
    WALLET_CHALLENGE_NOT_FOUND = "wallet_challenge_not_found"
    WALLET_CHALLENGE_EXPIRED = "wallet_challenge_expired"
    WALLET_CHALLENGE_USED = "wallet_challenge_used"
    WALLET_CHALLENGE_REVOKED = "wallet_challenge_revoked"
    WALLET_INTENT_MISMATCH = "wallet_intent_mismatch"
    WALLET_ORIGIN_MISMATCH = "wallet_origin_mismatch"
    WALLET_POLICY_HASH_MISMATCH = "wallet_policy_hash_mismatch"
    WALLET_PRINCIPAL_REVOKED = "wallet_principal_revoked"
    WALLET_DEVICE_BINDING_REQUIRED = "wallet_device_binding_required"
    STRONGER_WALLET_PROOF_REQUIRED = "stronger_wallet_proof_required"
    WALLET_STEP_UP_REQUIRED = "wallet_step_up_required"


class WalletProofVerificationError(ValueError):
    """Safe verifier error that never embeds raw proof material."""


@dataclass(frozen=True, slots=True)
class WalletCompatibilityContext:
    wallet_compatibility_id: str | None = None
    wallet_name: str | None = None
    wallet_version: str | None = None
    supported_proof_methods: tuple[str, ...] = ()
    known_quirks: tuple[str, ...] = ()
    maximum_allowed_risk_level: str | None = None


@dataclass(frozen=True, slots=True)
class WalletProofVerificationRequest:
    intent_payload: Mapping[str, object]
    intent_hash: str
    proof_type: WalletProofType
    signature: str
    wallet_identifier: str
    network: WalletNetwork
    expected_origin: str
    expected_action: WalletAuthAction
    expected_challenge_id: str
    expected_nonce_hash: str
    device_key_fingerprint: str
    requested_verification_strength: WalletVerificationStrength
    verification_context: Mapping[str, object]
    current_time: datetime
    script_type_hint: WalletScriptType = WalletScriptType.UNKNOWN
    public_key_hint: str | None = None
    hardware_wallet_claim: Mapping[str, object] | None = None
    air_gapped_claim: Mapping[str, object] | None = None
    quorum_claim: Mapping[str, object] | None = None
    access_certificate_fingerprint: str | None = None
    wallet_compatibility: WalletCompatibilityContext | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.intent_payload, Mapping):
            raise WalletProofVerificationError("wallet_proof_invalid_intent")
        if not str(self.intent_hash).startswith("sha256:"):
            raise WalletProofVerificationError("wallet_proof_invalid_intent_hash")
        _reject_secret_like(self.wallet_identifier, "wallet_identifier")
        _reject_secret_like(self.device_key_fingerprint, "device_key_fingerprint")
        _reject_secret_mapping(self.intent_payload, "intent_payload")
        _reject_secret_mapping(self.verification_context, "verification_context")
        if self.current_time.tzinfo is None:
            raise WalletProofVerificationError("wallet_proof_time_must_be_timezone_aware")
        if str(self.signature).strip() == "":
            raise WalletProofVerificationError("wallet_proof_signature_required")

    def safe_summary(self) -> dict[str, object]:
        return {
            "proof_type": self.proof_type.value,
            "intent_hash": self.intent_hash,
            "wallet_identifier": redact_wallet_identifier(self.wallet_identifier),
            "network": self.network.value,
            "expected_origin": self.expected_origin,
            "expected_action": self.expected_action.value,
            "expected_challenge_id": self.expected_challenge_id,
            "expected_nonce_hash": self.expected_nonce_hash,
            "device_key_fingerprint": self.device_key_fingerprint,
            "requested_verification_strength": self.requested_verification_strength.value,
            "signature": "<redacted>",
        }

    def __repr__(self) -> str:
        return f"WalletProofVerificationRequest({self.safe_summary()!r})"


@dataclass(frozen=True, slots=True)
class WalletProofVerificationResult:
    verified: bool
    proof_type: WalletProofType
    verifier_id: str
    verifier_version: str
    verification_strength: WalletVerificationStrength
    wallet_network: WalletNetwork
    script_type: WalletScriptType
    wallet_identifier_hash: str
    proof_fingerprint: str
    intent_hash: str
    verified_at: datetime
    reason_code: WalletProofVerificationReason
    limitations: tuple[str, ...] = ()
    policy_hints: tuple[str, ...] = ()
    evidence: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _reject_secret_mapping(self.evidence, "evidence")
        if self.verified and self.reason_code not in {
            WalletProofVerificationReason.VERIFIED,
            WalletProofVerificationReason.VALID_BIP322_PROOF,
        }:
            raise WalletProofVerificationError("wallet_proof_verified_result_reason_mismatch")

    def safe_summary(self) -> dict[str, object]:
        return {
            "verified": self.verified,
            "proof_type": self.proof_type.value,
            "verifier_id": self.verifier_id,
            "verifier_version": self.verifier_version,
            "verification_strength": self.verification_strength.value,
            "wallet_network": self.wallet_network.value,
            "script_type": self.script_type.value,
            "wallet_identifier_hash": self.wallet_identifier_hash,
            "proof_fingerprint": self.proof_fingerprint,
            "intent_hash": self.intent_hash,
            "reason_code": self.reason_code.value,
            "limitations": list(self.limitations),
            "policy_hints": list(self.policy_hints),
        }

    @classmethod
    def unsupported(
        cls,
        *,
        request: WalletProofVerificationRequest,
        verifier_id: str,
        verifier_version: str,
        reason_code: WalletProofVerificationReason = WalletProofVerificationReason.UNSUPPORTED_PROOF_TYPE,
        limitations: Sequence[str] = (),
    ) -> WalletProofVerificationResult:
        return cls(
            verified=False,
            proof_type=request.proof_type,
            verifier_id=verifier_id,
            verifier_version=verifier_version,
            verification_strength=WalletVerificationStrength.COMPATIBILITY,
            wallet_network=request.network,
            script_type=request.script_type_hint,
            wallet_identifier_hash=wallet_identifier_hash_for_request(request),
            proof_fingerprint=proof_fingerprint_for_request(request),
            intent_hash=request.intent_hash,
            verified_at=request.current_time,
            reason_code=reason_code,
            limitations=tuple(limitations),
            policy_hints=("policy_engine_required", "no_session_issued", "no_api_access_granted"),
            evidence={},
        )


class WalletProofVerifier(Protocol):
    proof_type: WalletProofType
    verifier_id: str
    verifier_version: str
    supported_networks: tuple[WalletNetwork, ...]
    supported_script_types: tuple[WalletScriptType, ...]
    maximum_verification_strength: WalletVerificationStrength

    def verify(self, request: WalletProofVerificationRequest) -> WalletProofVerificationResult: ...


class WalletProofRevocationChecker(Protocol):
    def is_revoked(self, *, target_type: str, target_hash: str, high_risk: bool = False) -> bool: ...


class WalletProofRevocationUnavailable(Exception):
    """Raised by revocation boundary when lookup cannot be completed."""


class WalletProofVerificationMetrics(Protocol):
    def record_verification(self, *, proof_type: str, verifier_id: str, network: str, result: str, verification_strength: str) -> None: ...


def wallet_identifier_hash_for_request(request: WalletProofVerificationRequest, server_pepper: str = "wallet-proof-interface") -> str:
    return compute_address_lookup_hash(server_pepper, request.wallet_identifier, request.network.value)


def proof_fingerprint_for_request(request: WalletProofVerificationRequest) -> str:
    return compute_wallet_proof_hash(request.signature, request.proof_type.value)


def _reject_secret_like(value: object, field_name: str) -> None:
    if isinstance(value, str):
        try:
            reject_forbidden_wallet_secret_input(value, field_name)
        except ValueError as exc:
            raise WalletProofVerificationError(f"forbidden wallet secret material in {field_name}") from exc


def _reject_secret_mapping(value: object, path: str) -> None:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        value = dataclasses.asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).lower()
            if key_text in {"seed", "private_key", "mnemonic", "xprv", "wallet_seed", "bitcoin_seed"}:
                raise WalletProofVerificationError(f"forbidden wallet secret material in {path}")
            _reject_secret_mapping(item, f"{path}.{key_text}")
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _reject_secret_mapping(item, path)
    elif isinstance(value, str):
        if value in {REQUIRED_SIGNATURE_WARNING, DEDICATED_AUTH_ADDRESS_WARNING}:
            return
        _reject_secret_like(value, path)


def redact_verification_exception(exc: Exception) -> WalletProofVerificationError:
    return WalletProofVerificationError(redact_sensitive_auth_material(str(exc)))
