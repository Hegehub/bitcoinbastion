"""BIP-322 wallet proof verifier for structured Bastion auth intents.

A valid result from this verifier means only that the selected BIP-322 backend
validated the submitted proof for the exact canonical intent and claimed script.
It does not create sessions, principals, entitlements, or API authorization and
it never asks for or accepts Bitcoin seed/private-key material.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum

from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.proofs import WalletProofType, WalletScriptType, WalletVerificationStrength
from app.services.access.crypto.hashing import constant_time_equal, sha256_prefixed
from app.services.wallet_auth.auth_intent import canonical_intent_json
from app.services.wallet_auth.privacy_commitments import compute_script_pubkey_commitment, redact_wallet_identifier
from app.services.wallet_auth.verifiers.base import (
    WalletProofVerificationReason,
    WalletProofVerificationRequest,
    WalletProofVerificationResult,
    proof_fingerprint_for_request,
    wallet_identifier_hash_for_request,
)
from app.services.wallet_auth.verifiers.bip322_backend import (
    BIP322ScriptBackend,
    ConservativeBIP322ScriptBackend,
    ScriptVerificationOutcome,
)
from app.services.wallet_auth.verifiers.bip322_codec import (
    BIP322CodecError,
    BIP322Variant,
    MAX_BIP322_MESSAGE_BYTES,
    MAX_BIP322_SIGNATURE_BYTES,
    ParsedBIP322Signature,
    bip322_message_hash,
    decode_bitcoin_address,
    decode_witness_stack,
    parse_bip322_signature,
)
from app.services.wallet_auth.verifiers.bip322_transactions import build_bip322_virtual_transactions

logger = logging.getLogger(__name__)

BIP322_VERIFIER_ID = "bip322"
BIP322_VERIFIER_VERSION = "1"


class VerificationOutcome(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True, slots=True)
class BIP322VerifierConfig:
    allow_prefixless_simple: bool = False
    allow_full: bool = True
    allow_proof_of_funds: bool = False
    max_message_bytes: int = MAX_BIP322_MESSAGE_BYTES
    max_signature_bytes: int = MAX_BIP322_SIGNATURE_BYTES


@dataclass(frozen=True, slots=True)
class BIP322Verifier:
    backend: BIP322ScriptBackend = ConservativeBIP322ScriptBackend()
    config: BIP322VerifierConfig = BIP322VerifierConfig()
    proof_type: WalletProofType = WalletProofType.BIP322
    verifier_id: str = BIP322_VERIFIER_ID
    verifier_version: str = BIP322_VERIFIER_VERSION
    supported_networks: tuple[WalletNetwork, ...] = tuple(WalletNetwork)
    supported_script_types: tuple[WalletScriptType, ...] = (
        WalletScriptType.P2WPKH,
        WalletScriptType.P2TR,
        WalletScriptType.P2WSH,
        WalletScriptType.UNKNOWN,
    )
    maximum_verification_strength: WalletVerificationStrength = WalletVerificationStrength.STANDARD

    def verify(self, request: WalletProofVerificationRequest) -> WalletProofVerificationResult:
        try:
            return self._verify(request)
        except BIP322CodecError as exc:
            return self._result(request, False, VerificationOutcome.INVALID, _reason_for_code(exc.reason_code), exc.reason_code)
        except Exception:
            logger.warning(
                "wallet_bip322_verification_failed",
                extra={"proof_type": self.proof_type.value, "reason_code": "internal_verifier_error"},
            )
            return self._result(
                request,
                False,
                VerificationOutcome.INVALID,
                WalletProofVerificationReason.INTERNAL_VERIFICATION_ERROR,
                "internal_verifier_error",
            )

    def _verify(self, request: WalletProofVerificationRequest) -> WalletProofVerificationResult:
        if request.proof_type != WalletProofType.BIP322:
            return self._result(
                request,
                False,
                VerificationOutcome.INVALID,
                WalletProofVerificationReason.UNSUPPORTED_PROOF_TYPE,
                "unsupported_proof_type",
            )
        canonical_message = canonical_intent_json(request.intent_payload)
        if len(canonical_message.encode("utf-8")) > self.config.max_message_bytes:
            return self._result(request, False, VerificationOutcome.INVALID, WalletProofVerificationReason.MALFORMED_PROOF, "message_too_large")
        if len(request.signature.encode("utf-8")) > self.config.max_signature_bytes:
            return self._result(request, False, VerificationOutcome.INVALID, WalletProofVerificationReason.MALFORMED_PROOF, "signature_too_large")
        parsed = parse_bip322_signature(request.signature, allow_prefixless_simple=self.config.allow_prefixless_simple)
        decoded_address = decode_bitcoin_address(request.wallet_identifier, request.network)
        if request.script_type_hint is not WalletScriptType.UNKNOWN and request.script_type_hint != decoded_address.script_type:
            return self._result(
                request,
                False,
                VerificationOutcome.INVALID,
                WalletProofVerificationReason.UNSUPPORTED_SCRIPT_TYPE,
                "script_mismatch",
                script_type=decoded_address.script_type,
                parsed=parsed,
            )
        message_hash = bip322_message_hash(canonical_message)
        virtual_txs = build_bip322_virtual_transactions(message_hash=message_hash, message_challenge=decoded_address.script_pubkey)
        if parsed.variant == BIP322Variant.PROOF_OF_FUNDS:
            return self._result(
                request,
                False,
                VerificationOutcome.INCONCLUSIVE,
                WalletProofVerificationReason.PROOF_OF_FUNDS_NOT_ALLOWED_FOR_AUTH,
                "proof_of_funds_not_allowed_for_auth",
                script_type=decoded_address.script_type,
                parsed=parsed,
                limitations=("proof_of_funds_not_authorization",),
            )
        if parsed.variant == BIP322Variant.FULL:
            if not self.config.allow_full:
                return self._result(
                    request,
                    False,
                    VerificationOutcome.INCONCLUSIVE,
                    WalletProofVerificationReason.UNSUPPORTED_SCRIPT_TYPE,
                    "full_variant_disabled",
                    script_type=decoded_address.script_type,
                    parsed=parsed,
                )
            backend_result = self.backend.verify_full(
                to_spend=virtual_txs.to_spend,
                to_sign=virtual_txs.to_sign,
                message_challenge=decoded_address.script_pubkey,
                payload=parsed.payload,
                script_type=decoded_address.script_type,
            )
        else:
            witness_stack = decode_witness_stack(parsed.payload)
            backend_result = self.backend.verify_simple(
                to_spend=virtual_txs.to_spend,
                to_sign=virtual_txs.to_sign,
                message_challenge=decoded_address.script_pubkey,
                witness_stack=witness_stack,
                script_type=decoded_address.script_type,
            )
        outcome = _map_backend_outcome(backend_result.outcome)
        verified = outcome == VerificationOutcome.VALID
        reason = WalletProofVerificationReason.VALID_BIP322_PROOF if verified else _reason_for_code(backend_result.reason_code)
        return self._result(
            request,
            verified,
            outcome,
            reason,
            backend_result.reason_code,
            script_type=decoded_address.script_type,
            parsed=parsed,
            limitations=backend_result.limitations,
            subject_commitment=compute_script_pubkey_commitment(decoded_address.script_pubkey.hex()),
            valid_at_time=backend_result.valid_at_time,
            valid_at_age=backend_result.valid_at_age,
            extra_evidence={"to_spend_txid": virtual_txs.to_spend_txid, "to_sign_txid": virtual_txs.to_sign_txid},
        )

    def _result(
        self,
        request: WalletProofVerificationRequest,
        verified: bool,
        outcome: VerificationOutcome,
        reason: WalletProofVerificationReason,
        bip322_reason_code: str,
        *,
        script_type: WalletScriptType | None = None,
        parsed: ParsedBIP322Signature | None = None,
        limitations: tuple[str, ...] = (),
        subject_commitment: str | None = None,
        valid_at_time: int | None = None,
        valid_at_age: int | None = None,
        extra_evidence: dict[str, object] | None = None,
    ) -> WalletProofVerificationResult:
        all_limitations = tuple(
            dict.fromkeys(
                (*limitations, "bip322_proof_is_not_authorization", "policy_engine_required", "no_session_issued", *(parsed.limitations if parsed else ()))
            )
        )
        evidence: dict[str, object] = {
            "outcome": outcome.value,
            "variant": parsed.variant.value if parsed else None,
            "bip322_reason_code": bip322_reason_code,
            "prefixless": parsed.prefixless if parsed else False,
            "backend_id": getattr(self.backend, "backend_id", "unknown"),
            "backend_version": getattr(self.backend, "backend_version", "unknown"),
        }
        if subject_commitment is not None:
            evidence["subject_commitment"] = subject_commitment
        if valid_at_time is not None:
            evidence["valid_at_time"] = valid_at_time
        if valid_at_age is not None:
            evidence["valid_at_age"] = valid_at_age
        if extra_evidence:
            evidence.update(extra_evidence)
        logger.info(
            "wallet_bip322_verification_result",
            extra={
                "proof_type": self.proof_type.value,
                "variant": parsed.variant.value if parsed else None,
                "script_type": (script_type or request.script_type_hint).value,
                "network": request.network.value,
                "outcome": outcome.value,
                "reason_code": reason.value,
                "wallet_identifier": redact_wallet_identifier(request.wallet_identifier),
            },
        )
        return WalletProofVerificationResult(
            verified=verified,
            proof_type=request.proof_type,
            verifier_id=self.verifier_id,
            verifier_version=self.verifier_version,
            verification_strength=WalletVerificationStrength.STANDARD if verified else WalletVerificationStrength.COMPATIBILITY,
            wallet_network=request.network,
            script_type=script_type or request.script_type_hint,
            wallet_identifier_hash=wallet_identifier_hash_for_request(request),
            proof_fingerprint=proof_fingerprint_for_request(request),
            intent_hash=request.intent_hash,
            verified_at=request.current_time,
            reason_code=reason,
            limitations=all_limitations,
            policy_hints=("policy_engine_required", "device_binding_required", "pop_session_required", "subscription_entitlement_required"),
            evidence=evidence,
        )


def validate_bip322_message_binding(intent_hash: str, canonical_message: str) -> bool:
    return constant_time_equal(intent_hash, sha256_prefixed(canonical_message))


def _map_backend_outcome(outcome: ScriptVerificationOutcome) -> VerificationOutcome:
    if outcome == ScriptVerificationOutcome.VALID:
        return VerificationOutcome.VALID
    if outcome == ScriptVerificationOutcome.INVALID:
        return VerificationOutcome.INVALID
    return VerificationOutcome.INCONCLUSIVE


def _reason_for_code(code: str) -> WalletProofVerificationReason:
    mapping = {
        "valid_bip322_proof": WalletProofVerificationReason.VALID_BIP322_PROOF,
        "invalid_base64": WalletProofVerificationReason.INVALID_BASE64,
        "empty_signature": WalletProofVerificationReason.EMPTY_SIGNATURE,
        "unknown_variant": WalletProofVerificationReason.UNKNOWN_VARIANT,
        "prefix_required": WalletProofVerificationReason.PREFIX_REQUIRED,
        "wrong_variant_payload": WalletProofVerificationReason.WRONG_VARIANT_PAYLOAD,
        "truncated_witness": WalletProofVerificationReason.WRONG_VARIANT_PAYLOAD,
        "invalid_address": WalletProofVerificationReason.INVALID_ADDRESS,
        "wrong_network": WalletProofVerificationReason.WRONG_NETWORK,
        "unsupported_script": WalletProofVerificationReason.UNSUPPORTED_SCRIPT,
        "unsupported_taproot_script_path": WalletProofVerificationReason.UNSUPPORTED_TAPROOT_SCRIPT_PATH,
        "script_backend_unavailable": WalletProofVerificationReason.SCRIPT_BACKEND_UNAVAILABLE,
        "message_mismatch": WalletProofVerificationReason.MESSAGE_MISMATCH,
        "script_mismatch": WalletProofVerificationReason.SCRIPT_MISMATCH,
        "invalid_signature": WalletProofVerificationReason.INVALID_SIGNATURE,
        "empty_witness": WalletProofVerificationReason.INVALID_SIGNATURE,
        "invalid_transaction_structure": WalletProofVerificationReason.INVALID_TRANSACTION_STRUCTURE,
        "forbidden_sighash": WalletProofVerificationReason.FORBIDDEN_SIGHASH,
        "non_canonical_signature": WalletProofVerificationReason.NON_CANONICAL_SIGNATURE,
        "timelock_not_supported": WalletProofVerificationReason.TIMELOCK_NOT_SUPPORTED,
        "proof_of_funds_not_allowed_for_auth": WalletProofVerificationReason.PROOF_OF_FUNDS_NOT_ALLOWED_FOR_AUTH,
        "message_too_large": WalletProofVerificationReason.MALFORMED_PROOF,
        "signature_too_large": WalletProofVerificationReason.MALFORMED_PROOF,
    }
    return mapping.get(code, WalletProofVerificationReason.MALFORMED_PROOF)
