"""Hardware wallet assurance composition and policy context helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.domain.wallet_auth.actions import WalletAuthAction
from app.domain.wallet_auth.hardware import (
    HardwareWalletAssuranceLevel,
    HardwareWalletEvidenceStatus,
    HardwareWalletEvidenceType,
    HardwareWalletIntentDisplayState,
)
from app.domain.wallet_auth.proofs import WalletProofType, WalletVerificationStrength
from app.services.wallet_auth.hardware_evidence import HardwareEvidenceContext, HardwareEvidenceVerifier
from app.services.wallet_auth.verifiers.base import WalletProofVerificationResult
from app.schemas.hardware_wallet import HardwareWalletClaim, VerifiedHardwareWalletEvidence

LOGIN_HARDWARE_EVIDENCE_TTL = timedelta(hours=24)
NEW_DEVICE_HARDWARE_EVIDENCE_TTL = timedelta(minutes=5)
HIGH_RISK_HARDWARE_EVIDENCE_TTL = timedelta(minutes=5)
CRITICAL_HARDWARE_EVIDENCE_TTL = timedelta(minutes=2)


@dataclass(frozen=True, slots=True)
class HardwareWalletEligibilityFlags:
    login_eligible: bool
    new_device_eligible: bool
    session_creation_eligible: bool
    step_up_eligible: bool
    api_key_creation_eligible: bool
    recovery_factor_eligible: bool
    business_owner_action_eligible: bool
    payregister_admin_eligible: bool
    treasury_policy_eligible: bool
    enterprise_policy_eligible: bool
    sovereign_quorum_eligible: bool
    offline_pack_eligible: bool
    access_certificate_binding_eligible: bool


@dataclass(frozen=True, slots=True)
class WalletProofAssuranceResult:
    cryptographic_proof_valid: bool
    proof_type: WalletProofType
    base_verification_strength: WalletVerificationStrength
    hardware_evidence_status: HardwareWalletEvidenceStatus
    hardware_assurance: HardwareWalletAssuranceLevel
    effective_verification_strength: WalletVerificationStrength
    eligibility_flags: HardwareWalletEligibilityFlags
    limitations: tuple[str, ...]
    policy_requirements_remaining: tuple[str, ...]
    evidence_fingerprint: str | None


@dataclass(frozen=True, slots=True)
class HardwareWalletPolicyContext:
    evidence_status: HardwareWalletEvidenceStatus
    hardware_assurance: HardwareWalletAssuranceLevel
    effective_verification_strength: WalletVerificationStrength
    intent_display_state: HardwareWalletIntentDisplayState
    proof_freshness: str
    evidence_freshness: str
    requested_action: str
    risk_level: str
    eligibility_flags: HardwareWalletEligibilityFlags
    limitations: tuple[str, ...]
    evidence_fingerprint: str | None


class HardwareAssuranceEvaluator:
    def __init__(self, verifiers: tuple[HardwareEvidenceVerifier, ...]) -> None:
        self.verifiers = verifiers

    def evaluate(
        self,
        *,
        verified_proof: WalletProofVerificationResult,
        structured_intent: Mapping[str, object],
        hardware_claim: HardwareWalletClaim,
        context: HardwareEvidenceContext,
        compatibility_record: Mapping[str, object] | None = None,
        requested_action: WalletAuthAction | str,
        risk_level: str,
        policy_context: Mapping[str, object] | None = None,
    ) -> WalletProofAssuranceResult:
        evidence = self._verify_evidence(hardware_claim, context)
        limitations = list(evidence.limitations)
        if not verified_proof.verified:
            limitations.append("underlying_wallet_proof_invalid")
            assurance = HardwareWalletAssuranceLevel.UNKNOWN
            effective = WalletVerificationStrength.COMPATIBILITY
        else:
            assurance = self._assurance_after_policy(evidence, risk_level, policy_context or {})
            effective = self._effective_strength(verified_proof, assurance)
        if _is_evidence_expired(evidence, context.now, requested_action, risk_level):
            limitations.append("hardware_evidence_expired")
            assurance = HardwareWalletAssuranceLevel.CLAIMED if assurance != HardwareWalletAssuranceLevel.UNKNOWN else assurance
        if _binding_mismatch(evidence, context, structured_intent):
            limitations.append("hardware_binding_mismatch")
            assurance = HardwareWalletAssuranceLevel.UNKNOWN
            effective = WalletVerificationStrength.COMPATIBILITY
        flags = _eligibility_flags(verified_proof.verified, assurance, WalletAuthAction(str(requested_action)) if str(requested_action) in WalletAuthAction._value2member_map_ else requested_action, risk_level)
        remaining = _policy_requirements_remaining(verified_proof, assurance, risk_level)
        return WalletProofAssuranceResult(
            cryptographic_proof_valid=verified_proof.verified,
            proof_type=verified_proof.proof_type,
            base_verification_strength=verified_proof.verification_strength,
            hardware_evidence_status=evidence.evidence_status,
            hardware_assurance=assurance,
            effective_verification_strength=effective,
            eligibility_flags=flags,
            limitations=tuple(dict.fromkeys((*limitations, "policy_engine_final_authority", "pop_session_required"))),
            policy_requirements_remaining=remaining,
            evidence_fingerprint=evidence.evidence_fingerprint,
        )

    def policy_context(self, *, result: WalletProofAssuranceResult, evidence: VerifiedHardwareWalletEvidence, requested_action: str, risk_level: str) -> HardwareWalletPolicyContext:
        return HardwareWalletPolicyContext(
            evidence_status=result.hardware_evidence_status,
            hardware_assurance=result.hardware_assurance,
            effective_verification_strength=result.effective_verification_strength,
            intent_display_state=evidence.intent_display_state,
            proof_freshness="freshness_checked_by_challenge_service",
            evidence_freshness="fresh" if result.hardware_evidence_status is HardwareWalletEvidenceStatus.VERIFIED else "not_fresh_or_unverified",
            requested_action=requested_action,
            risk_level=risk_level,
            eligibility_flags=result.eligibility_flags,
            limitations=result.limitations,
            evidence_fingerprint=result.evidence_fingerprint,
        )

    def _verify_evidence(self, claim: HardwareWalletClaim, context: HardwareEvidenceContext) -> VerifiedHardwareWalletEvidence:
        for verifier in self.verifiers:
            if verifier.supports(claim):
                return verifier.verify(claim, context)
        return self.verifiers[0].verify(claim, context)

    def _assurance_after_policy(
        self,
        evidence: VerifiedHardwareWalletEvidence,
        risk_level: str,
        policy_context: Mapping[str, object],
    ) -> HardwareWalletAssuranceLevel:
        if evidence.evidence_status not in {HardwareWalletEvidenceStatus.VERIFIED, HardwareWalletEvidenceStatus.PARTIALLY_VERIFIED}:
            return evidence.effective_assurance
        if evidence.evidence_type is HardwareWalletEvidenceType.DEVICE_DISPLAY_CONFIRMATION:
            return HardwareWalletAssuranceLevel.HARDWARE_ASSISTED
        if evidence.evidence_type in {HardwareWalletEvidenceType.VENDOR_ATTESTATION, HardwareWalletEvidenceType.SECURE_ELEMENT_ATTESTATION}:
            return HardwareWalletAssuranceLevel.HARDWARE_VERIFIED if policy_context.get("vendor_trust_root_configured") is True else HardwareWalletAssuranceLevel.CLAIMED
        if evidence.evidence_type is HardwareWalletEvidenceType.AIR_GAPPED_ARTIFACT:
            return HardwareWalletAssuranceLevel.AIR_GAPPED if policy_context.get("air_gapped_ceremony_verified") is True else HardwareWalletAssuranceLevel.CLAIMED
        if evidence.evidence_type is HardwareWalletEvidenceType.MULTI_DEVICE_QUORUM:
            return HardwareWalletAssuranceLevel.SOVEREIGN if policy_context.get("policy_quorum_satisfied") is True and risk_level == "critical" else HardwareWalletAssuranceLevel.AIR_GAPPED
        return evidence.effective_assurance

    def _effective_strength(
        self,
        verified_proof: WalletProofVerificationResult,
        assurance: HardwareWalletAssuranceLevel,
    ) -> WalletVerificationStrength:
        if not verified_proof.verified:
            return WalletVerificationStrength.COMPATIBILITY
        if assurance in {HardwareWalletAssuranceLevel.HARDWARE_VERIFIED, HardwareWalletAssuranceLevel.AIR_GAPPED}:
            return WalletVerificationStrength.HIGH_ASSURANCE
        if assurance is HardwareWalletAssuranceLevel.SOVEREIGN:
            return WalletVerificationStrength.SOVEREIGN
        return verified_proof.verification_strength


def _is_evidence_expired(evidence: VerifiedHardwareWalletEvidence, now: datetime, requested_action: WalletAuthAction | str, risk_level: str) -> bool:
    if evidence.expires_at is None:
        return False
    ttl = LOGIN_HARDWARE_EVIDENCE_TTL
    if str(requested_action) in {WalletAuthAction.NEW_DEVICE.value, WalletAuthAction.DEVICE_ADD.value}:
        ttl = NEW_DEVICE_HARDWARE_EVIDENCE_TTL
    if risk_level == "high":
        ttl = HIGH_RISK_HARDWARE_EVIDENCE_TTL
    if risk_level == "critical":
        ttl = CRITICAL_HARDWARE_EVIDENCE_TTL
    return evidence.expires_at.astimezone(UTC) < now.astimezone(UTC) or now.astimezone(UTC) - evidence.issued_at.astimezone(UTC) > ttl


def _binding_mismatch(evidence: VerifiedHardwareWalletEvidence, context: HardwareEvidenceContext, structured_intent: Mapping[str, object]) -> bool:
    return not evidence.evidence_fingerprint or context.requested_action != str(structured_intent.get("action", context.requested_action))


def _eligibility_flags(proof_valid: bool, assurance: HardwareWalletAssuranceLevel, requested_action: WalletAuthAction | str, risk_level: str) -> HardwareWalletEligibilityFlags:
    claimed_or_better = assurance in {
        HardwareWalletAssuranceLevel.CLAIMED,
        HardwareWalletAssuranceLevel.STANDARD,
        HardwareWalletAssuranceLevel.HARDWARE_ASSISTED,
        HardwareWalletAssuranceLevel.HARDWARE_VERIFIED,
        HardwareWalletAssuranceLevel.AIR_GAPPED,
        HardwareWalletAssuranceLevel.SOVEREIGN,
    }
    assisted = assurance in {
        HardwareWalletAssuranceLevel.HARDWARE_ASSISTED,
        HardwareWalletAssuranceLevel.HARDWARE_VERIFIED,
        HardwareWalletAssuranceLevel.AIR_GAPPED,
        HardwareWalletAssuranceLevel.SOVEREIGN,
    }
    verified = assurance in {HardwareWalletAssuranceLevel.HARDWARE_VERIFIED, HardwareWalletAssuranceLevel.AIR_GAPPED, HardwareWalletAssuranceLevel.SOVEREIGN}
    sovereign = assurance is HardwareWalletAssuranceLevel.SOVEREIGN
    high_risk = risk_level in {"high", "critical", "sovereign"}
    return HardwareWalletEligibilityFlags(
        login_eligible=proof_valid and claimed_or_better,
        new_device_eligible=proof_valid and assisted and not high_risk,
        session_creation_eligible=proof_valid,
        step_up_eligible=proof_valid and assisted,
        api_key_creation_eligible=proof_valid and verified,
        recovery_factor_eligible=proof_valid and verified,
        business_owner_action_eligible=proof_valid and verified,
        payregister_admin_eligible=proof_valid and verified,
        treasury_policy_eligible=proof_valid and verified,
        enterprise_policy_eligible=proof_valid and verified,
        sovereign_quorum_eligible=proof_valid and sovereign,
        offline_pack_eligible=proof_valid and verified,
        access_certificate_binding_eligible=proof_valid and verified,
    )


def _policy_requirements_remaining(
    verified_proof: WalletProofVerificationResult,
    assurance: HardwareWalletAssuranceLevel,
    risk_level: str,
) -> tuple[str, ...]:
    requirements = ["policy_engine_decision", "device_binding", "pop_session", "subscription_entitlement"]
    if not verified_proof.verified:
        requirements.append("valid_wallet_proof")
    if risk_level in {"high", "critical"} and assurance in {HardwareWalletAssuranceLevel.UNKNOWN, HardwareWalletAssuranceLevel.CLAIMED}:
        requirements.append("stronger_wallet_proof_or_verified_hardware_evidence")
    if risk_level == "critical" and assurance not in {HardwareWalletAssuranceLevel.HARDWARE_VERIFIED, HardwareWalletAssuranceLevel.AIR_GAPPED, HardwareWalletAssuranceLevel.SOVEREIGN}:
        requirements.append("critical_action_hardware_or_quorum_requirement")
    return tuple(requirements)
