from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.domain.wallet_auth.actions import WalletAuthAction
from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.proofs import WalletProofType, WalletVerificationStrength
from app.services.wallet_auth.auth_intent import build_wallet_auth_intent, hash_intent
from app.services.wallet_auth.proof_verifier import WalletProofVerifierRegistry, build_default_placeholder_registry
from app.services.wallet_auth.verifiers.base import WalletProofVerificationReason, WalletProofVerificationRequest
from app.services.wallet_auth.verifiers.legacy_message import (
    LEGACY_SIGNATURE_FORBIDDEN_ACTIONS,
    LegacyBitcoinMessageVerifier,
    LegacyBitcoinMessageVerifierConfig,
    LegacySignatureOutcome,
    LegacySignatureVerification,
)

VECTORS = json.loads(Path("tests/fixtures/wallet_auth/legacy_message/vectors.json").read_text())


@dataclass(frozen=True)
class AllowingBackend:
    backend_id: str = "allowing_legacy_test_backend"
    backend_version: str = "test"

    def verify(self, **kwargs):
        return LegacySignatureVerification(LegacySignatureOutcome.VALID, "verified")


def request(action: WalletAuthAction = WalletAuthAction.LOGIN, *, plan: str = "lite", strength: WalletVerificationStrength = WalletVerificationStrength.COMPATIBILITY):
    now = datetime(2026, 7, 13, 12, tzinfo=UTC)
    intent = build_wallet_auth_intent(
        domain="auth.bitcoin-bastion.com",
        action=action.value,
        purpose=action.value,
        origin="https://auth.bitcoin-bastion.com",
        network=WalletNetwork.BITCOIN_MAINNET.value,
        challenge_id="legacy-challenge-1",
        nonce="legacy-nonce-123",
        device_key_fingerprint="device:fingerprint",
        policy_hash="sha256:" + "b" * 64,
        risk_level="low",
        wallet_proof_type=WalletProofType.LEGACY_MESSAGE_SIGNATURE.value,
        issued_at=now,
        expires_at=now + timedelta(minutes=5),
    )
    payload = intent.__dict__.copy()
    return WalletProofVerificationRequest(
        intent_payload=payload,
        intent_hash=hash_intent(payload),
        proof_type=WalletProofType.LEGACY_MESSAGE_SIGNATURE,
        signature=VECTORS["valid_signature"],
        wallet_identifier=VECTORS["wallet_identifier"],
        network=WalletNetwork.BITCOIN_MAINNET,
        expected_origin="https://auth.bitcoin-bastion.com",
        expected_action=action,
        expected_challenge_id="legacy-challenge-1",
        expected_nonce_hash="sha256:e2778752b1d38894a0ea3ef014df0eec61df259cc18e053ca38b56e0ffeccd0e",
        device_key_fingerprint="device:fingerprint",
        requested_verification_strength=strength,
        verification_context={"subscription_plan": plan},
        current_time=now + timedelta(minutes=1),
    )


def verifier() -> LegacyBitcoinMessageVerifier:
    return LegacyBitcoinMessageVerifier(
        backend=AllowingBackend(),
        config=LegacyBitcoinMessageVerifierConfig(allow_legacy_signatures=True),
    )


def test_forbidden_critical_actions_are_declared_and_rejected():
    critical = [
        WalletAuthAction.CREATE_API_KEY,
        WalletAuthAction.TREASURY_POLICY_CHANGE,
        WalletAuthAction.RECOVERY_COMPLETE,
        WalletAuthAction.LOCKDOWN_RELEASE,
        WalletAuthAction.DEVICE_ADD,
        WalletAuthAction.PAYREGISTER_ADMIN_ENABLE,
        WalletAuthAction.BUSINESS_ROLE_ASSIGNMENT,
        WalletAuthAction.ENTERPRISE_POLICY_CHANGE,
        WalletAuthAction.OFFLINE_PACK_ISSUE,
    ]
    for action in critical:
        assert action in LEGACY_SIGNATURE_FORBIDDEN_ACTIONS
        result = verifier().verify(request(action))
        assert result.verified is False
        assert result.reason_code == WalletProofVerificationReason.LEGACY_SIGNATURE_NOT_ALLOWED_FOR_ACTION


def test_business_enterprise_sovereign_and_stronger_strength_are_rejected():
    for plan in ("business", "enterprise", "sovereign"):
        assert verifier().verify(request(plan=plan)).reason_code == WalletProofVerificationReason.LEGACY_SIGNATURE_NOT_ALLOWED_FOR_PLAN
    for strength in (WalletVerificationStrength.STANDARD, WalletVerificationStrength.HIGH_ASSURANCE, WalletVerificationStrength.SOVEREIGN):
        result = verifier().verify(request(strength=strength))
        assert result.reason_code == WalletProofVerificationReason.STRONGER_WALLET_PROOF_REQUIRED
        assert result.verification_strength == WalletVerificationStrength.COMPATIBILITY


def test_wallet_signature_alone_keeps_pop_device_and_policy_mandatory():
    result = verifier().verify(request())
    assert result.verified is True
    assert result.verification_strength == WalletVerificationStrength.COMPATIBILITY
    assert result.evidence["requires_device_binding"] is True
    assert result.evidence["requires_pop_session"] is True
    assert result.evidence["requires_policy_decision"] is True
    assert "pop_session_required" in result.policy_hints
    assert "policy_engine_required" in result.policy_hints


def test_no_automatic_downgrade_from_bip322_to_legacy():
    registry = build_default_placeholder_registry()
    bip322_request = replace(request(), proof_type=WalletProofType.BIP322, signature="not-a-bip322-proof")
    result = registry.verify(bip322_request)
    assert result.verifier_id == "bip322"
    assert result.verified is False
    assert result.proof_type == WalletProofType.BIP322


def test_enabled_legacy_verifier_must_be_explicitly_registered():
    registry = WalletProofVerifierRegistry()
    registry.register(verifier())
    result = registry.verify(request())
    assert result.verified is True
    assert result.proof_type == WalletProofType.LEGACY_MESSAGE_SIGNATURE


def test_tampered_origin_device_and_policy_fail_safely():
    base = request()
    cases = [
        replace(base, intent_payload={**base.intent_payload, "origin": "https://evil.example"}),
        replace(base, intent_payload={**base.intent_payload, "device_key_fingerprint": "other"}),
        replace(base, intent_payload={**base.intent_payload, "policy_hash": "bad"}),
    ]
    for item in cases:
        assert verifier().verify(item).verified is False
