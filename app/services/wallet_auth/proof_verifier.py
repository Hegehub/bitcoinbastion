"""Wallet proof verifier registry and pre-validation orchestration.

This module dispatches to explicitly registered proof adapters only. It does not
implement BIP-322, legacy Bitcoin message verification, LNURL-auth callback
verification, hardware attestation, multi-wallet quorum, session issuance,
principal creation, entitlement checks, or Policy Engine authorization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast
from datetime import UTC, datetime, timedelta

from app.domain.wallet_auth.actions import is_critical_wallet_action
from app.domain.wallet_auth.constants import REQUIRED_SIGNATURE_WARNING, WALLET_AUTH_INTENT_VERSION
from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.proofs import (
    WalletProofType,
    WalletScriptType,
    WalletVerificationStrength,
    is_strength_at_least,
)
from app.services.access.crypto.hashing import constant_time_equal, sha256_prefixed
from app.services.wallet_auth.auth_intent import hash_intent, validate_intent
from app.services.wallet_auth.verifiers.base import (
    WalletProofRevocationChecker,
    WalletProofRevocationUnavailable,
    WalletProofVerificationMetrics,
    WalletProofVerificationReason,
    WalletProofVerificationRequest,
    WalletProofVerificationResult,
    WalletProofVerifier,
    proof_fingerprint_for_request,
    wallet_identifier_hash_for_request,
)

_FUTURE_TOLERANCE = timedelta(minutes=5)
_STANDARD_POLICY_HINTS = ("policy_engine_required", "device_binding_required", "pop_session_required", "subscription_entitlement_required")


class WalletProofVerifierRegistryError(ValueError):
    """Safe registry error with machine-readable message only."""


@dataclass(frozen=True, slots=True)
class PlaceholderWalletProofVerifier:
    proof_type: WalletProofType
    verifier_id: str
    verifier_version: str
    future_prompt: str
    supported_networks: tuple[WalletNetwork, ...] = tuple(WalletNetwork)
    supported_script_types: tuple[WalletScriptType, ...] = (WalletScriptType.P2WPKH, WalletScriptType.P2TR, WalletScriptType.UNKNOWN)
    maximum_verification_strength: WalletVerificationStrength = WalletVerificationStrength.COMPATIBILITY

    def verify(self, request: WalletProofVerificationRequest) -> WalletProofVerificationResult:
        return WalletProofVerificationResult.unsupported(
            request=request,
            verifier_id=self.verifier_id,
            verifier_version=self.verifier_version,
            reason_code=WalletProofVerificationReason.NOT_IMPLEMENTED,
            limitations=(f"cryptographic implementation deferred to {self.future_prompt}", "placeholder_never_returns_verified"),
        )


class BIP322VerifierStub(PlaceholderWalletProofVerifier):
    def __init__(self) -> None:
        super().__init__(WalletProofType.BIP322, "bip322_stub", "0", "Prompt 11/72")


class LegacyMessageVerifierStub(PlaceholderWalletProofVerifier):
    def __init__(self) -> None:
        super().__init__(WalletProofType.LEGACY_MESSAGE_SIGNATURE, "legacy_message_stub", "0", "Prompt 12/72")


class HardwareWalletVerifierStub(PlaceholderWalletProofVerifier):
    def __init__(self) -> None:
        super().__init__(WalletProofType.HARDWARE_WALLET, "hardware_wallet_stub", "0", "Prompt 13/72")


class AirGappedVerifierStub(PlaceholderWalletProofVerifier):
    def __init__(self) -> None:
        super().__init__(WalletProofType.AIR_GAPPED, "air_gapped_stub", "0", "Prompt 59/72")


class MultisigQuorumVerifierStub(PlaceholderWalletProofVerifier):
    def __init__(self) -> None:
        super().__init__(WalletProofType.MULTISIG_QUORUM, "multisig_quorum_stub", "0", "Prompt 59/72")


class LNURLAuthBridgeVerifierStub(PlaceholderWalletProofVerifier):
    def __init__(self) -> None:
        super().__init__(WalletProofType.LNURL_AUTH, "lnurl_auth_bridge_stub", "0", "Prompts 21/72-26/72")


class AccessCertificateBridgeVerifierStub(PlaceholderWalletProofVerifier):
    def __init__(self) -> None:
        super().__init__(WalletProofType.ACCESS_CERTIFICATE_BRIDGE, "access_certificate_bridge_stub", "0", "Prompt 60/72")


class WalletProofVerifierRegistry:
    def __init__(
        self,
        *,
        revocation_checker: WalletProofRevocationChecker | None = None,
        metrics: WalletProofVerificationMetrics | None = None,
    ) -> None:
        self._verifiers: dict[WalletProofType, WalletProofVerifier] = {}
        self.revocation_checker = revocation_checker
        self.metrics = metrics

    def register(self, verifier: WalletProofVerifier) -> None:
        existing = self._verifiers.get(verifier.proof_type)
        if existing is not None and (
            existing.verifier_id != verifier.verifier_id or existing.verifier_version != verifier.verifier_version
        ):
            raise WalletProofVerifierRegistryError("wallet_proof_verifier_duplicate")
        self._verifiers[verifier.proof_type] = verifier

    def get(self, proof_type: WalletProofType | str) -> WalletProofVerifier:
        proof = WalletProofType(proof_type)
        verifier = self._verifiers.get(proof)
        if verifier is None:
            raise WalletProofVerifierRegistryError("wallet_proof_unsupported")
        return verifier

    def supported_proof_types(self) -> tuple[WalletProofType, ...]:
        return tuple(sorted(self._verifiers, key=lambda proof: proof.value))

    def verify(self, request: WalletProofVerificationRequest) -> WalletProofVerificationResult:
        try:
            verifier = self.get(request.proof_type)
        except Exception:
            result = _failure(request, "registry", "0", WalletProofVerificationReason.UNSUPPORTED_PROOF_TYPE)
            self._record_metric(request, result)
            return result
        precheck = self.prevalidate_intent(request, verifier)
        if precheck is not None:
            self._record_metric(request, precheck)
            return precheck
        revoked = self._check_revocation(request)
        if revoked is not None:
            self._record_metric(request, revoked)
            return revoked
        try:
            result = verifier.verify(request)
        except Exception:
            result = _failure(request, verifier.verifier_id, verifier.verifier_version, WalletProofVerificationReason.INTERNAL_VERIFICATION_ERROR)
        if result.verified and not is_strength_at_least(result.verification_strength, request.requested_verification_strength):
            result = _failure(
                request,
                verifier.verifier_id,
                verifier.verifier_version,
                WalletProofVerificationReason.VERIFICATION_STRENGTH_INSUFFICIENT,
                limitations=("verified proof weaker than requested context",),
            )
        self._record_metric(request, result)
        return result

    def prevalidate_intent(
        self,
        request: WalletProofVerificationRequest,
        verifier: WalletProofVerifier,
    ) -> WalletProofVerificationResult | None:
        payload = request.intent_payload
        if not payload:
            return _failure(request, verifier.verifier_id, verifier.verifier_version, WalletProofVerificationReason.MALFORMED_PROOF)
        if request.network not in verifier.supported_networks:
            return _failure(request, verifier.verifier_id, verifier.verifier_version, WalletProofVerificationReason.UNSUPPORTED_NETWORK)
        if request.script_type_hint not in verifier.supported_script_types and WalletScriptType.UNKNOWN not in verifier.supported_script_types:
            return _failure(request, verifier.verifier_id, verifier.verifier_version, WalletProofVerificationReason.UNSUPPORTED_SCRIPT_TYPE)
        if not constant_time_equal(hash_intent(payload), request.intent_hash):
            return _failure(request, verifier.verifier_id, verifier.verifier_version, WalletProofVerificationReason.INTENT_HASH_MISMATCH)
        issued_at = _coerce_datetime(payload.get("issued_at"))
        expires_at = _coerce_datetime(payload.get("expires_at"))
        now = request.current_time.astimezone(UTC)
        if issued_at > now + _FUTURE_TOLERANCE:
            return _failure(request, verifier.verifier_id, verifier.verifier_version, WalletProofVerificationReason.INTENT_NOT_YET_VALID)
        if expires_at <= now:
            return _failure(request, verifier.verifier_id, verifier.verifier_version, WalletProofVerificationReason.INTENT_EXPIRED)
        validation = validate_intent(payload)
        if not validation.valid:
            return _failure(request, verifier.verifier_id, verifier.verifier_version, WalletProofVerificationReason.MALFORMED_PROOF, limitations=validation.errors)
        if payload.get("version") != WALLET_AUTH_INTENT_VERSION:
            return _failure(request, verifier.verifier_id, verifier.verifier_version, WalletProofVerificationReason.MALFORMED_PROOF)
        if payload.get("origin") not in {None, "", request.expected_origin}:
            return _failure(request, verifier.verifier_id, verifier.verifier_version, WalletProofVerificationReason.ORIGIN_MISMATCH)
        if payload.get("action") != request.expected_action.value:
            return _failure(request, verifier.verifier_id, verifier.verifier_version, WalletProofVerificationReason.ACTION_MISMATCH)
        if payload.get("network") not in {None, "", request.network.value}:
            return _failure(request, verifier.verifier_id, verifier.verifier_version, WalletProofVerificationReason.UNSUPPORTED_NETWORK)
        if payload.get("challenge_id") != request.expected_challenge_id:
            return _failure(request, verifier.verifier_id, verifier.verifier_version, WalletProofVerificationReason.CHALLENGE_MISMATCH)
        nonce = payload.get("nonce")
        nonce_hash = payload.get("nonce_hash")
        if isinstance(nonce, str) and nonce and not constant_time_equal(sha256_prefixed(nonce), request.expected_nonce_hash):
            return _failure(request, verifier.verifier_id, verifier.verifier_version, WalletProofVerificationReason.NONCE_MISMATCH)
        if nonce in {None, ""} and nonce_hash != request.expected_nonce_hash:
            return _failure(request, verifier.verifier_id, verifier.verifier_version, WalletProofVerificationReason.NONCE_MISMATCH)
        if payload.get("device_key_fingerprint") != request.device_key_fingerprint:
            return _failure(request, verifier.verifier_id, verifier.verifier_version, WalletProofVerificationReason.DEVICE_MISMATCH)
        warnings_value = payload.get("warnings")
        warnings = tuple(warnings_value) if isinstance(warnings_value, (list, tuple)) else ()
        if REQUIRED_SIGNATURE_WARNING not in warnings:  # stable safety binding
            return _failure(request, verifier.verifier_id, verifier.verifier_version, WalletProofVerificationReason.MALFORMED_PROOF)
        if request.proof_type == WalletProofType.LEGACY_MESSAGE_SIGNATURE and is_critical_wallet_action(request.expected_action):
            return _failure(
                request,
                verifier.verifier_id,
                verifier.verifier_version,
                WalletProofVerificationReason.VERIFICATION_STRENGTH_INSUFFICIENT,
                limitations=("compatibility proof cannot satisfy critical action",),
            )
        return None

    def _check_revocation(self, request: WalletProofVerificationRequest) -> WalletProofVerificationResult | None:
        if self.revocation_checker is None:
            return None
        high_risk = request.requested_verification_strength in {
            WalletVerificationStrength.HIGH_ASSURANCE,
            WalletVerificationStrength.SOVEREIGN,
        }
        targets = (
            ("wallet_proof", proof_fingerprint_for_request(request)),
            ("wallet_identifier", wallet_identifier_hash_for_request(request)),
            ("verifier_proof_type", request.proof_type.value),
        )
        try:
            for target_type, target_hash in targets:
                if self.revocation_checker.is_revoked(target_type=target_type, target_hash=target_hash, high_risk=high_risk):
                    return _failure(request, "revocation", "0", WalletProofVerificationReason.PROOF_REVOKED)
        except WalletProofRevocationUnavailable:
            if high_risk:
                return _failure(request, "revocation", "0", WalletProofVerificationReason.VERIFIER_UNAVAILABLE)
        return None

    def _record_metric(self, request: WalletProofVerificationRequest, result: WalletProofVerificationResult) -> None:
        if self.metrics is None:
            return
        self.metrics.record_verification(
            proof_type=request.proof_type.value,
            verifier_id=result.verifier_id,
            network=request.network.value,
            result=result.reason_code.value,
            verification_strength=result.verification_strength.value,
        )


def build_default_placeholder_registry() -> WalletProofVerifierRegistry:
    from app.services.wallet_auth.verifiers.bip322 import BIP322Verifier
    from app.services.wallet_auth.verifiers.legacy_message import LegacyBitcoinMessageVerifier

    registry = WalletProofVerifierRegistry()
    for verifier in (
        BIP322Verifier(),
        LegacyBitcoinMessageVerifier(),
        HardwareWalletVerifierStub(),
        AirGappedVerifierStub(),
        MultisigQuorumVerifierStub(),
        LNURLAuthBridgeVerifierStub(),
        AccessCertificateBridgeVerifierStub(),
    ):
        registry.register(cast(WalletProofVerifier, verifier))
    return registry


def _failure(
    request: WalletProofVerificationRequest,
    verifier_id: str,
    verifier_version: str,
    reason: WalletProofVerificationReason,
    *,
    limitations: tuple[str, ...] = (),
) -> WalletProofVerificationResult:
    return WalletProofVerificationResult(
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
        reason_code=reason,
        limitations=tuple(limitations),
        policy_hints=_STANDARD_POLICY_HINTS,
        evidence={},
    )


def _coerce_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        result = value
    elif isinstance(value, str):
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    else:
        raise WalletProofVerifierRegistryError("wallet_proof_invalid_time")
    if result.tzinfo is None:
        result = result.replace(tzinfo=UTC)
    return result.astimezone(UTC)
