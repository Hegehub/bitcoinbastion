from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.domain.wallet_auth.actions import WalletAuthAction
from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.proofs import WalletProofType, WalletScriptType, WalletVerificationStrength
from app.services.wallet_auth.auth_intent import build_wallet_auth_intent, hash_intent
from app.services.wallet_auth.verifiers.base import WalletProofVerificationReason, WalletProofVerificationRequest
from app.services.wallet_auth.verifiers.legacy_message import (
    LEGACY_SIGNATURE_ALLOWED_ACTIONS,
    LegacyBitcoinMessageVerifier,
    LegacyBitcoinMessageVerifierConfig,
    LegacySignatureOutcome,
    LegacySignatureVerification,
)

VECTORS = json.loads(Path("tests/fixtures/wallet_auth/legacy_message/vectors.json").read_text())


@dataclass(frozen=True)
class FixtureBackend:
    backend_id: str = "fixture_legacy_backend"
    backend_version: str = "test"

    def verify(self, *, canonical_message, signature, wallet_identifier, network, script_type):
        if signature == VECTORS["valid_signature"] and wallet_identifier == VECTORS["wallet_identifier"] and script_type == WalletScriptType.P2PKH:
            return LegacySignatureVerification(LegacySignatureOutcome.VALID, "verified")
        return LegacySignatureVerification(LegacySignatureOutcome.INVALID, "invalid_legacy_signature")


def _request(*, signature: str | None = None, action: WalletAuthAction = WalletAuthAction.LOGIN, network: WalletNetwork = WalletNetwork.BITCOIN_MAINNET, wallet_identifier: str | None = None, plan: str = "lite", risk: str = "low"):
    now = datetime(2026, 7, 13, 12, tzinfo=UTC)
    intent = build_wallet_auth_intent(
        domain="auth.bitcoin-bastion.com",
        action=action.value,
        purpose=action.value,
        origin="https://auth.bitcoin-bastion.com",
        network=network.value,
        challenge_id="legacy-challenge-1",
        nonce="legacy-nonce-123",
        device_key_fingerprint="device:fingerprint",
        policy_hash="sha256:" + "b" * 64,
        risk_level=risk,
        wallet_proof_type=WalletProofType.LEGACY_MESSAGE_SIGNATURE.value,
        issued_at=now,
        expires_at=now + timedelta(minutes=5),
    )
    payload = intent.__dict__.copy()
    return WalletProofVerificationRequest(
        intent_payload=payload,
        intent_hash=hash_intent(payload),
        proof_type=WalletProofType.LEGACY_MESSAGE_SIGNATURE,
        signature=signature or VECTORS["valid_signature"],
        wallet_identifier=wallet_identifier or VECTORS["wallet_identifier"],
        network=network,
        expected_origin="https://auth.bitcoin-bastion.com",
        expected_action=action,
        expected_challenge_id="legacy-challenge-1",
        expected_nonce_hash="sha256:e2778752b1d38894a0ea3ef014df0eec61df259cc18e053ca38b56e0ffeccd0e",
        device_key_fingerprint="device:fingerprint",
        requested_verification_strength=WalletVerificationStrength.COMPATIBILITY,
        verification_context={"subscription_plan": plan},
        current_time=now + timedelta(minutes=1),
        script_type_hint=WalletScriptType.UNKNOWN,
    )


def _verifier(enabled: bool = True) -> LegacyBitcoinMessageVerifier:
    return LegacyBitcoinMessageVerifier(
        backend=FixtureBackend(),
        config=LegacyBitcoinMessageVerifierConfig(allow_legacy_signatures=enabled),
    )


def test_feature_flag_disabled_by_default_rejects_verification():
    result = LegacyBitcoinMessageVerifier(backend=FixtureBackend()).verify(_request())
    assert result.verified is False
    assert result.reason_code == WalletProofVerificationReason.LEGACY_SIGNATURE_DISABLED


def test_valid_supported_legacy_signature_is_compatibility_only():
    result = _verifier().verify(_request())
    assert result.verified is True
    assert result.proof_type == WalletProofType.LEGACY_MESSAGE_SIGNATURE
    assert result.verification_strength == WalletVerificationStrength.COMPATIBILITY
    assert result.script_type == WalletScriptType.P2PKH
    assert result.evidence["requires_device_binding"] is True
    assert result.evidence["requires_pop_session"] is True
    assert result.evidence["requires_policy_decision"] is True
    assert result.evidence["high_risk_allowed"] is False
    assert VECTORS["wallet_identifier"] not in result.wallet_identifier_hash


def test_low_risk_allowed_actions_are_explicit():
    assert WalletAuthAction.LOGIN in LEGACY_SIGNATURE_ALLOWED_ACTIONS
    assert WalletAuthAction.REGISTER in LEGACY_SIGNATURE_ALLOWED_ACTIONS
    assert WalletAuthAction.LINK in LEGACY_SIGNATURE_ALLOWED_ACTIONS


@pytest.mark.parametrize("signature", [VECTORS["malformed_signature"], "not base64!"])
def test_malformed_or_invalid_base64_rejected(signature: str):
    result = _verifier().verify(_request(signature=signature))
    assert result.verified is False
    assert result.reason_code == WalletProofVerificationReason.MALFORMED_LEGACY_SIGNATURE


def test_invalid_signature_and_changed_intent_rejected():
    result = _verifier().verify(_request(signature=VECTORS["invalid_signature"]))
    assert result.verified is False
    assert result.reason_code == WalletProofVerificationReason.INVALID_LEGACY_SIGNATURE
    req = _request()
    tampered = replace(req, intent_payload={**req.intent_payload, "action": WalletAuthAction.REGISTER.value})
    result = _verifier().verify(tampered)
    assert result.verified is False
    assert result.reason_code == WalletProofVerificationReason.WALLET_INTENT_MISMATCH


def test_wrong_network_and_unsupported_address_type_rejected():
    wrong_network = _verifier().verify(_request(network=WalletNetwork.BITCOIN_TESTNET))
    assert wrong_network.reason_code == WalletProofVerificationReason.WALLET_NETWORK_MISMATCH
    unsupported = _verifier().verify(_request(wallet_identifier=VECTORS["unsupported_address"]))
    assert unsupported.reason_code == WalletProofVerificationReason.UNSUPPORTED_ADDRESS_TYPE


def test_plan_policy_strength_and_risk_restrictions():
    assert _verifier().verify(_request(plan="business")).reason_code == WalletProofVerificationReason.LEGACY_SIGNATURE_NOT_ALLOWED_FOR_PLAN
    req = _request()
    stronger = replace(req, requested_verification_strength=WalletVerificationStrength.STANDARD)
    assert _verifier().verify(stronger).reason_code == WalletProofVerificationReason.STRONGER_WALLET_PROOF_REQUIRED
    critical = replace(req, intent_payload={**req.intent_payload, "risk_level": "critical"})
    assert _verifier().verify(critical).reason_code == WalletProofVerificationReason.WALLET_STEP_UP_REQUIRED
