from __future__ import annotations

from datetime import UTC, datetime, timedelta
from dataclasses import replace

from app.domain.wallet_auth.actions import WalletAuthAction
from app.domain.wallet_auth.hardware import (
    HardwareWalletAssuranceLevel,
    HardwareWalletEvidenceStatus,
    HardwareWalletEvidenceType,
    HardwareWalletIntentDisplayState,
    HardwareWalletInteractionMode,
)
from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.proofs import WalletProofType, WalletScriptType, WalletVerificationStrength
from app.schemas.hardware_wallet import HardwareWalletClaim
from app.services.wallet_auth.hardware_assurance import HardwareAssuranceEvaluator
from app.services.wallet_auth.hardware_evidence import (
    AirGappedArtifactVerifier,
    DeviceDisplayEvidenceVerifier,
    HardwareEvidenceContext,
    NoEvidenceVerifier,
    SelfClaimedHardwareVerifier,
    VendorAttestationVerifier,
)
from app.services.wallet_auth.verifiers.base import WalletProofVerificationReason, WalletProofVerificationResult

NOW = datetime(2026, 7, 13, 12, tzinfo=UTC)


def proof(verified: bool = True, strength: WalletVerificationStrength = WalletVerificationStrength.STANDARD) -> WalletProofVerificationResult:
    return WalletProofVerificationResult(
        verified=verified,
        proof_type=WalletProofType.BIP322,
        verifier_id="test",
        verifier_version="1",
        verification_strength=strength,
        wallet_network=WalletNetwork.BITCOIN_MAINNET,
        script_type=WalletScriptType.P2WPKH,
        wallet_identifier_hash="hmac-sha256:" + "a" * 64,
        proof_fingerprint="sha256:" + "b" * 64,
        intent_hash="sha256:" + "c" * 64,
        verified_at=NOW,
        reason_code=WalletProofVerificationReason.VERIFIED if verified else WalletProofVerificationReason.INVALID_SIGNATURE,
        limitations=(),
        policy_hints=("policy_engine_required",),
    )


def context(action: str = "login", principal: str = "hmac-sha256:" + "a" * 64, device: str = "sha256:" + "d" * 64) -> HardwareEvidenceContext:
    return HardwareEvidenceContext(
        principal_hash=principal,
        device_key_fingerprint=device,
        proof_method="bip322",
        proof_reference_hash="sha256:" + "b" * 64,
        structured_intent={"domain": "auth.bitcoin-bastion.com", "action": action, "expires_at": (NOW + timedelta(minutes=5)).isoformat(), "warnings": ["safe"], "requested_scopes": [], "risk_level": "low", "policy_hash": "sha256:" + "e" * 64},
        origin="https://auth.bitcoin-bastion.com",
        domain="auth.bitcoin-bastion.com",
        requested_action=action,
        risk_level="low",
        policy_epoch="policy-1",
        now=NOW,
    )


def evaluator() -> HardwareAssuranceEvaluator:
    return HardwareAssuranceEvaluator((NoEvidenceVerifier(), SelfClaimedHardwareVerifier(), DeviceDisplayEvidenceVerifier(), VendorAttestationVerifier(), AirGappedArtifactVerifier()))


def claim(evidence_type: HardwareWalletEvidenceType, **kwargs) -> HardwareWalletClaim:
    data = {
        "interaction_mode": HardwareWalletInteractionMode.QR,
        "evidence_type": evidence_type,
        "intent_display_state": HardwareWalletIntentDisplayState.FULLY_DISPLAYED,
        "proof_method": "bip322",
        "metadata": {"displayed_fields": ["domain", "action", "expires_at", "warnings", "requested_scopes", "risk_level", "policy_hash"]},
    }
    data.update(kwargs)
    return HardwareWalletClaim(**data)


def test_no_evidence_and_self_claim_do_not_raise_high_assurance():
    no_evidence = evaluator().evaluate(verified_proof=proof(), structured_intent=context().structured_intent, hardware_claim=claim(HardwareWalletEvidenceType.NONE), context=context(), requested_action=WalletAuthAction.LOGIN, risk_level="low")
    assert no_evidence.hardware_assurance is HardwareWalletAssuranceLevel.UNKNOWN
    self_claim = evaluator().evaluate(verified_proof=proof(), structured_intent=context().structured_intent, hardware_claim=claim(HardwareWalletEvidenceType.SELF_CLAIMED, requested_assurance=HardwareWalletAssuranceLevel.SOVEREIGN), context=context(), requested_action=WalletAuthAction.LOGIN, risk_level="low")
    assert self_claim.hardware_assurance is HardwareWalletAssuranceLevel.CLAIMED
    assert not self_claim.eligibility_flags.sovereign_quorum_eligible


def test_full_display_may_produce_hardware_assisted_but_not_hardware_verified():
    result = evaluator().evaluate(verified_proof=proof(), structured_intent=context().structured_intent, hardware_claim=claim(HardwareWalletEvidenceType.DEVICE_DISPLAY_CONFIRMATION), context=context(), requested_action=WalletAuthAction.LOGIN, risk_level="low")
    assert result.hardware_assurance is HardwareWalletAssuranceLevel.HARDWARE_ASSISTED
    assert result.effective_verification_strength is WalletVerificationStrength.STANDARD
    assert result.eligibility_flags.step_up_eligible


def test_vendor_and_air_gapped_extensions_fail_safely_without_policy():
    vendor = evaluator().evaluate(verified_proof=proof(), structured_intent=context().structured_intent, hardware_claim=claim(HardwareWalletEvidenceType.VENDOR_ATTESTATION), context=context(), requested_action=WalletAuthAction.LOGIN, risk_level="low")
    assert vendor.hardware_evidence_status is HardwareWalletEvidenceStatus.UNSUPPORTED
    air = evaluator().evaluate(verified_proof=proof(), structured_intent=context().structured_intent, hardware_claim=claim(HardwareWalletEvidenceType.AIR_GAPPED_ARTIFACT), context=context(), requested_action=WalletAuthAction.LOGIN, risk_level="low")
    assert air.hardware_assurance is HardwareWalletAssuranceLevel.UNKNOWN


def test_high_and_critical_risk_restrictions_and_invalid_underlying_proof():
    self_claim = evaluator().evaluate(verified_proof=proof(strength=WalletVerificationStrength.COMPATIBILITY), structured_intent=context().structured_intent, hardware_claim=claim(HardwareWalletEvidenceType.SELF_CLAIMED), context=context(), requested_action=WalletAuthAction.TREASURY_POLICY_CHANGE, risk_level="critical")
    assert "critical_action_hardware_or_quorum_requirement" in self_claim.policy_requirements_remaining
    invalid = evaluator().evaluate(verified_proof=proof(False), structured_intent=context().structured_intent, hardware_claim=claim(HardwareWalletEvidenceType.DEVICE_DISPLAY_CONFIRMATION), context=context(), requested_action=WalletAuthAction.LOGIN, risk_level="low")
    assert "underlying_wallet_proof_invalid" in invalid.limitations
    assert invalid.effective_verification_strength is WalletVerificationStrength.COMPATIBILITY


def test_evidence_binding_and_freshness_rules():
    login_ctx = context("login")
    result = evaluator().evaluate(verified_proof=proof(), structured_intent={**login_ctx.structured_intent, "action": "treasury_policy_change"}, hardware_claim=claim(HardwareWalletEvidenceType.DEVICE_DISPLAY_CONFIRMATION), context=login_ctx, requested_action=WalletAuthAction.LOGIN, risk_level="low")
    assert "hardware_binding_mismatch" in result.limitations
    expired_ctx = replace(login_ctx, now=NOW + timedelta(days=1))
    expired = evaluator().evaluate(verified_proof=proof(), structured_intent=expired_ctx.structured_intent, hardware_claim=claim(HardwareWalletEvidenceType.DEVICE_DISPLAY_CONFIRMATION, evidence_expires_at=NOW), context=expired_ctx, requested_action=WalletAuthAction.LOGIN, risk_level="low")
    assert "hardware_evidence_expired" in expired.limitations
