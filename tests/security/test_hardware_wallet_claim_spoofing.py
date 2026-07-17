from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.domain.wallet_auth.actions import WalletAuthAction
from app.domain.wallet_auth.hardware import HardwareWalletAssuranceLevel, HardwareWalletEvidenceType, HardwareWalletInteractionMode
from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.proofs import WalletProofType, WalletScriptType, WalletVerificationStrength
from app.schemas.hardware_wallet import HardwareWalletClaim
from app.services.wallet_auth.hardware_assurance import HardwareAssuranceEvaluator
from app.services.wallet_auth.hardware_evidence import DeviceDisplayEvidenceVerifier, HardwareEvidenceContext, NoEvidenceVerifier, SelfClaimedHardwareVerifier
from app.services.wallet_auth.verifiers.base import WalletProofVerificationReason, WalletProofVerificationResult

NOW = datetime(2026, 7, 13, 12, tzinfo=UTC)


def proof() -> WalletProofVerificationResult:
    return WalletProofVerificationResult(
        verified=True,
        proof_type=WalletProofType.BIP322,
        verifier_id="test",
        verifier_version="1",
        verification_strength=WalletVerificationStrength.STANDARD,
        wallet_network=WalletNetwork.BITCOIN_MAINNET,
        script_type=WalletScriptType.P2WPKH,
        wallet_identifier_hash="hmac-sha256:" + "a" * 64,
        proof_fingerprint="sha256:" + "b" * 64,
        intent_hash="sha256:" + "c" * 64,
        verified_at=NOW,
        reason_code=WalletProofVerificationReason.VERIFIED,
    )


def context() -> HardwareEvidenceContext:
    return HardwareEvidenceContext(
        principal_hash="hmac-sha256:" + "a" * 64,
        device_key_fingerprint="sha256:" + "d" * 64,
        proof_method="bip322",
        proof_reference_hash="sha256:" + "b" * 64,
        structured_intent={"domain": "auth.bitcoin-bastion.com", "action": "login", "expires_at": (NOW + timedelta(minutes=5)).isoformat(), "warnings": ["safe"]},
        origin="https://auth.bitcoin-bastion.com",
        domain="auth.bitcoin-bastion.com",
        requested_action="login",
        risk_level="low",
        policy_epoch="policy-1",
        now=NOW,
    )


def evaluator() -> HardwareAssuranceEvaluator:
    return HardwareAssuranceEvaluator((NoEvidenceVerifier(), SelfClaimedHardwareVerifier(), DeviceDisplayEvidenceVerifier()))


def test_client_spoofed_claims_cannot_self_assign_high_assurance():
    malicious_claims = [
        {"metadata": {"hardware_wallet": True}},
        {"vendor_name": "trusted"},
        {"device_model": "secure"},
        {"metadata": {"attested": True}},
        {"requested_assurance": HardwareWalletAssuranceLevel.SOVEREIGN},
        {"interaction_mode": HardwareWalletInteractionMode.SD_CARD},
        {"metadata": {"full_display": True}},
    ]
    for extra in malicious_claims:
        claim = HardwareWalletClaim(evidence_type=HardwareWalletEvidenceType.SELF_CLAIMED, proof_method="bip322", **extra)
        result = evaluator().evaluate(verified_proof=proof(), structured_intent=context().structured_intent, hardware_claim=claim, context=context(), requested_action=WalletAuthAction.LOGIN, risk_level="low")
        assert result.hardware_assurance is HardwareWalletAssuranceLevel.CLAIMED
        assert not result.eligibility_flags.recovery_factor_eligible
        assert not result.eligibility_flags.treasury_policy_eligible
        assert not result.eligibility_flags.enterprise_policy_eligible
        assert not result.eligibility_flags.sovereign_quorum_eligible


def test_air_gapped_transport_claim_alone_is_not_air_gapped_assurance():
    claim = HardwareWalletClaim(evidence_type=HardwareWalletEvidenceType.SELF_CLAIMED, interaction_mode=HardwareWalletInteractionMode.QR, requested_assurance=HardwareWalletAssuranceLevel.AIR_GAPPED, proof_method="bip322")
    result = evaluator().evaluate(verified_proof=proof(), structured_intent=context().structured_intent, hardware_claim=claim, context=context(), requested_action=WalletAuthAction.LOGIN, risk_level="low")
    assert result.hardware_assurance is HardwareWalletAssuranceLevel.CLAIMED
    assert result.effective_verification_strength is WalletVerificationStrength.STANDARD
