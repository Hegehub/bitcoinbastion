"""Legacy Bitcoin Signed Message compatibility verifier.

This adapter is deliberately compatibility-only. It verifies only explicitly
requested ``legacy_message_signature`` proofs, never falls back from BIP-322,
never grants API access, and never upgrades assurance beyond compatibility.
"""

from __future__ import annotations

import base64
import hashlib
import logging
import os
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from app.domain.wallet_auth.actions import WalletAuthAction
from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.proofs import WalletProofType, WalletScriptType, WalletVerificationStrength
from app.services.access.crypto.hashing import constant_time_equal, sha256_prefixed
from app.services.wallet_auth.auth_intent import canonical_intent_json
from app.services.wallet_auth.privacy_commitments import redact_wallet_identifier
from app.services.wallet_auth.verifiers.base import (
    WalletProofVerificationReason,
    WalletProofVerificationRequest,
    WalletProofVerificationResult,
    proof_fingerprint_for_request,
    wallet_identifier_hash_for_request,
)

logger = logging.getLogger(__name__)

LEGACY_SIGNATURE_ENV_FLAG = "WALLET_AUTH_ALLOW_LEGACY_SIGNATURES"
LEGACY_MESSAGE_VERIFIER_ID = "legacy_bitcoin_message"
LEGACY_MESSAGE_VERIFIER_VERSION = "1"

LEGACY_SIGNATURE_ALLOWED_ACTIONS = frozenset(
    {
        WalletAuthAction.REGISTER,
        WalletAuthAction.LOGIN,
        WalletAuthAction.LINK,
    }
)
LEGACY_SIGNATURE_FORBIDDEN_ACTIONS = frozenset(
    {
        WalletAuthAction.CREATE_API_KEY,
        WalletAuthAction.INCREASE_SCOPE,
        WalletAuthAction.EXPORT_DATA,
        WalletAuthAction.CREATE_DELEGATED_PASS,
        WalletAuthAction.TREASURY_POLICY_CHANGE,
        WalletAuthAction.RECOVERY_COMPLETE,
        WalletAuthAction.LOCKDOWN_RELEASE,
        WalletAuthAction.BUSINESS_ROLE_ASSIGNMENT,
        WalletAuthAction.ENTERPRISE_POLICY_CHANGE,
        WalletAuthAction.PAYREGISTER_ADMIN_ENABLE,
        WalletAuthAction.OFFLINE_PACK_ISSUE,
        WalletAuthAction.NEW_DEVICE,
        WalletAuthAction.DEVICE_ADD,
        WalletAuthAction.STEP_UP,
    }
)
LEGACY_SIGNATURE_ALLOWED_PLANS = frozenset({"lite", "basic", "plus", "pro"})
LEGACY_SIGNATURE_FORBIDDEN_PLANS = frozenset({"business", "enterprise", "sovereign"})


class LegacySignatureOutcome(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class LegacySignatureVerification:
    outcome: LegacySignatureOutcome
    reason_code: str
    limitations: tuple[str, ...] = ()


class LegacyBitcoinMessageBackend(Protocol):
    @property
    def backend_id(self) -> str: ...

    @property
    def backend_version(self) -> str: ...

    def verify(
        self,
        *,
        canonical_message: str,
        signature: str,
        wallet_identifier: str,
        network: WalletNetwork,
        script_type: WalletScriptType,
    ) -> LegacySignatureVerification: ...


@dataclass(frozen=True, slots=True)
class ConservativeLegacyMessageBackend:
    """Default backend that fails closed until a recoverable secp256k1 verifier is configured."""

    backend_id: str = "conservative_legacy_message_backend"
    backend_version: str = "1"

    def verify(
        self,
        *,
        canonical_message: str,
        signature: str,
        wallet_identifier: str,
        network: WalletNetwork,
        script_type: WalletScriptType,
    ) -> LegacySignatureVerification:
        return LegacySignatureVerification(
            LegacySignatureOutcome.UNSUPPORTED,
            "unsupported_legacy_signature_format",
            ("recoverable_secp256k1_backend_required", "no_fake_cryptographic_success"),
        )


@dataclass(frozen=True, slots=True)
class LegacyBitcoinMessageVerifierConfig:
    allow_legacy_signatures: bool = False
    max_signature_bytes: int = 2048
    allowed_actions: frozenset[WalletAuthAction] = LEGACY_SIGNATURE_ALLOWED_ACTIONS
    forbidden_actions: frozenset[WalletAuthAction] = LEGACY_SIGNATURE_FORBIDDEN_ACTIONS
    allowed_plans: frozenset[str] = LEGACY_SIGNATURE_ALLOWED_PLANS
    forbidden_plans: frozenset[str] = LEGACY_SIGNATURE_FORBIDDEN_PLANS

    @classmethod
    def from_environment(cls) -> "LegacyBitcoinMessageVerifierConfig":
        enabled = os.getenv(LEGACY_SIGNATURE_ENV_FLAG, "false").strip().lower() in {"1", "true", "yes", "on"}
        return cls(allow_legacy_signatures=enabled)


@dataclass(frozen=True, slots=True)
class LegacyBitcoinMessageVerifier:
    backend: LegacyBitcoinMessageBackend = ConservativeLegacyMessageBackend()
    config: LegacyBitcoinMessageVerifierConfig = LegacyBitcoinMessageVerifierConfig()
    proof_type: WalletProofType = WalletProofType.LEGACY_MESSAGE_SIGNATURE
    verifier_id: str = LEGACY_MESSAGE_VERIFIER_ID
    verifier_version: str = LEGACY_MESSAGE_VERIFIER_VERSION
    supported_networks: tuple[WalletNetwork, ...] = tuple(WalletNetwork)
    supported_script_types: tuple[WalletScriptType, ...] = (WalletScriptType.P2PKH, WalletScriptType.UNKNOWN)
    maximum_verification_strength: WalletVerificationStrength = WalletVerificationStrength.COMPATIBILITY

    def verify(self, request: WalletProofVerificationRequest) -> WalletProofVerificationResult:
        if not self.config.allow_legacy_signatures:
            return self._failure(request, WalletProofVerificationReason.LEGACY_SIGNATURE_DISABLED, "legacy_signature_disabled")
        if request.proof_type != WalletProofType.LEGACY_MESSAGE_SIGNATURE:
            return self._failure(request, WalletProofVerificationReason.UNSUPPORTED_PROOF_TYPE, "unsupported_proof_type")
        context = self._check_intent_context(request)
        if context is not None:
            return context
        policy = self._check_policy(request)
        if policy is not None:
            return policy
        canonical_message = canonical_intent_json(request.intent_payload)
        try:
            address = _decode_legacy_address(request.wallet_identifier, request.network)
        except LegacyMessageAddressError as exc:
            code = str(exc)
            return self._failure(request, _legacy_reason(code), code)
        if address.script_type not in self.supported_script_types:
            return self._failure(
                request,
                WalletProofVerificationReason.UNSUPPORTED_ADDRESS_TYPE,
                "unsupported_address_type",
                script_type=address.script_type,
            )
        if len(request.signature.encode("utf-8")) > self.config.max_signature_bytes:
            return self._failure(request, WalletProofVerificationReason.MALFORMED_LEGACY_SIGNATURE, "malformed_legacy_signature")
        if not _looks_like_legacy_base64_signature(request.signature):
            return self._failure(request, WalletProofVerificationReason.MALFORMED_LEGACY_SIGNATURE, "malformed_legacy_signature")
        backend_result = self.backend.verify(
            canonical_message=canonical_message,
            signature=request.signature,
            wallet_identifier=request.wallet_identifier,
            network=request.network,
            script_type=address.script_type,
        )
        if backend_result.outcome == LegacySignatureOutcome.VALID:
            return self._success(request, address.script_type, backend_result.limitations)
        reason = _legacy_reason(backend_result.reason_code)
        return self._failure(request, reason, backend_result.reason_code, script_type=address.script_type, limitations=backend_result.limitations)

    def _check_intent_context(self, request: WalletProofVerificationRequest) -> WalletProofVerificationResult | None:
        payload = request.intent_payload
        if payload.get("origin") != request.expected_origin:
            return self._failure(request, WalletProofVerificationReason.WALLET_ORIGIN_MISMATCH, "wallet_origin_mismatch")
        if payload.get("action") != request.expected_action.value:
            return self._failure(request, WalletProofVerificationReason.WALLET_INTENT_MISMATCH, "wallet_intent_mismatch")
        if payload.get("network") != request.network.value:
            return self._failure(request, WalletProofVerificationReason.WALLET_NETWORK_MISMATCH, "wallet_network_mismatch")
        if payload.get("challenge_id") != request.expected_challenge_id:
            return self._failure(request, WalletProofVerificationReason.WALLET_INTENT_MISMATCH, "wallet_intent_mismatch")
        nonce = payload.get("nonce")
        if not isinstance(nonce, str) or not constant_time_equal(sha256_prefixed(nonce), request.expected_nonce_hash):
            return self._failure(request, WalletProofVerificationReason.WALLET_INTENT_MISMATCH, "wallet_intent_mismatch")
        if payload.get("device_key_fingerprint") != request.device_key_fingerprint:
            return self._failure(request, WalletProofVerificationReason.WALLET_DEVICE_BINDING_REQUIRED, "wallet_device_binding_required")
        policy_hash = payload.get("policy_hash")
        if not isinstance(policy_hash, str) or not policy_hash.startswith("sha256:"):
            return self._failure(request, WalletProofVerificationReason.WALLET_POLICY_HASH_MISMATCH, "wallet_policy_hash_mismatch")
        return None

    def _check_policy(self, request: WalletProofVerificationRequest) -> WalletProofVerificationResult | None:
        if request.expected_action in self.config.forbidden_actions or request.expected_action not in self.config.allowed_actions:
            return self._failure(
                request,
                WalletProofVerificationReason.LEGACY_SIGNATURE_NOT_ALLOWED_FOR_ACTION,
                "legacy_signature_not_allowed_for_action",
            )
        plan = str(request.verification_context.get("subscription_plan", "lite")).lower()
        if plan in self.config.forbidden_plans or plan not in self.config.allowed_plans:
            return self._failure(
                request,
                WalletProofVerificationReason.LEGACY_SIGNATURE_NOT_ALLOWED_FOR_PLAN,
                "legacy_signature_not_allowed_for_plan",
            )
        if request.requested_verification_strength != WalletVerificationStrength.COMPATIBILITY:
            return self._failure(
                request,
                WalletProofVerificationReason.STRONGER_WALLET_PROOF_REQUIRED,
                "stronger_wallet_proof_required",
            )
        risk = str(request.intent_payload.get("risk_level", "low")).lower()
        if risk in {"high", "critical", "sovereign"}:
            return self._failure(request, WalletProofVerificationReason.WALLET_STEP_UP_REQUIRED, "wallet_step_up_required")
        return None

    def _success(
        self,
        request: WalletProofVerificationRequest,
        script_type: WalletScriptType,
        limitations: tuple[str, ...],
    ) -> WalletProofVerificationResult:
        return self._result(request, True, WalletProofVerificationReason.VERIFIED, "verified", script_type, limitations)

    def _failure(
        self,
        request: WalletProofVerificationRequest,
        reason: WalletProofVerificationReason,
        internal_reason: str,
        *,
        script_type: WalletScriptType | None = None,
        limitations: tuple[str, ...] = (),
    ) -> WalletProofVerificationResult:
        return self._result(request, False, reason, internal_reason, script_type or request.script_type_hint, limitations)

    def _result(
        self,
        request: WalletProofVerificationRequest,
        verified: bool,
        reason: WalletProofVerificationReason,
        internal_reason: str,
        script_type: WalletScriptType,
        limitations: tuple[str, ...],
    ) -> WalletProofVerificationResult:
        all_limitations = tuple(
            dict.fromkeys(
                (
                    *limitations,
                    "legacy_signature_compatibility_only",
                    "bip322_preferred",
                    "requires_device_binding",
                    "requires_pop_session",
                    "requires_policy_decision",
                    "high_risk_allowed_false",
                )
            )
        )
        evidence = {
            "legacy_reason_code": internal_reason,
            "requires_device_binding": True,
            "requires_pop_session": True,
            "requires_policy_decision": True,
            "high_risk_allowed": False,
            "audit_events": (
                "legacy_wallet_proof_attempted",
                "legacy_wallet_proof_succeeded" if verified else "legacy_wallet_proof_failed",
            ),
            "revocation_targets": ("wallet_proof", "wallet_identifier_commitment", "wallet_principal", "wallet_device", "challenge"),
            "backend_id": getattr(self.backend, "backend_id", "unknown"),
            "backend_version": getattr(self.backend, "backend_version", "unknown"),
        }
        logger.info(
            "wallet_legacy_message_verification_result",
            extra={
                "proof_type": self.proof_type.value,
                "network": request.network.value,
                "script_type": script_type.value,
                "reason_code": reason.value,
                "wallet_identifier": redact_wallet_identifier(request.wallet_identifier),
            },
        )
        return WalletProofVerificationResult(
            verified=verified,
            proof_type=request.proof_type,
            verifier_id=self.verifier_id,
            verifier_version=self.verifier_version,
            verification_strength=WalletVerificationStrength.COMPATIBILITY,
            wallet_network=request.network,
            script_type=script_type,
            wallet_identifier_hash=wallet_identifier_hash_for_request(request),
            proof_fingerprint=proof_fingerprint_for_request(request),
            intent_hash=request.intent_hash,
            verified_at=request.current_time,
            reason_code=reason,
            limitations=all_limitations,
            policy_hints=("policy_engine_required", "device_binding_required", "pop_session_required", "legacy_low_risk_only"),
            evidence=evidence,
        )


@dataclass(frozen=True, slots=True)
class DecodedLegacyAddress:
    script_type: WalletScriptType
    network: WalletNetwork
    payload_hash: bytes


def _decode_legacy_address(address: str, expected_network: WalletNetwork) -> DecodedLegacyAddress:
    raw = _base58check_decode(address.strip())
    if len(raw) != 21:
        raise LegacyMessageAddressError("unsupported_address_type")
    version = raw[0]
    payload = raw[1:]
    if version == 0x00:
        network = WalletNetwork.BITCOIN_MAINNET
        script_type = WalletScriptType.P2PKH
    elif version == 0x6F:
        network = WalletNetwork.BITCOIN_TESTNET
        script_type = WalletScriptType.P2PKH
    elif version in {0x05, 0xC4}:
        raise LegacyMessageAddressError("unsupported_address_type")
    else:
        raise LegacyMessageAddressError("unsupported_address_type")
    if expected_network == WalletNetwork.BITCOIN_SIGNET and network == WalletNetwork.BITCOIN_TESTNET:
        network = WalletNetwork.BITCOIN_SIGNET
    if network != expected_network:
        raise LegacyMessageAddressError("wallet_network_mismatch")
    return DecodedLegacyAddress(script_type=script_type, network=network, payload_hash=payload)


class LegacyMessageAddressError(ValueError):
    pass


def _base58check_decode(value: str) -> bytes:
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    number = 0
    for char in value:
        if char not in alphabet:
            raise LegacyMessageAddressError("unsupported_address_type")
        number = number * 58 + alphabet.index(char)
    combined = number.to_bytes((number.bit_length() + 7) // 8, "big") if number else b""
    leading = len(value) - len(value.lstrip("1"))
    decoded = b"\x00" * leading + combined
    if len(decoded) < 5:
        raise LegacyMessageAddressError("unsupported_address_type")
    payload, checksum = decoded[:-4], decoded[-4:]
    expected = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    if checksum != expected:
        raise LegacyMessageAddressError("wallet_identifier_mismatch")
    return payload


def _looks_like_legacy_base64_signature(signature: str) -> bool:
    try:
        decoded = base64.b64decode(signature, validate=True)
    except Exception:
        return False
    return len(decoded) == 65 and 27 <= decoded[0] <= 42


def _legacy_reason(code: str) -> WalletProofVerificationReason:
    mapping = {
        "invalid_legacy_signature": WalletProofVerificationReason.INVALID_LEGACY_SIGNATURE,
        "malformed_legacy_signature": WalletProofVerificationReason.MALFORMED_LEGACY_SIGNATURE,
        "unsupported_legacy_signature_format": WalletProofVerificationReason.UNSUPPORTED_LEGACY_SIGNATURE_FORMAT,
        "unsupported_address_type": WalletProofVerificationReason.UNSUPPORTED_ADDRESS_TYPE,
        "wallet_network_mismatch": WalletProofVerificationReason.WALLET_NETWORK_MISMATCH,
        "wallet_identifier_mismatch": WalletProofVerificationReason.WALLET_IDENTIFIER_MISMATCH,
    }
    return mapping.get(code, WalletProofVerificationReason.INVALID_LEGACY_SIGNATURE)
