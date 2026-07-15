"""Canonical hardware-wallet evidence envelopes and verifier interfaces."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

from app.domain.wallet_auth.hardware import (
    HardwareWalletAssuranceLevel,
    HardwareWalletEvidenceStatus,
    HardwareWalletEvidenceType,
    HardwareWalletIntentDisplayState,
)
from app.services.access.crypto.hashing import canonical_json, sha256_prefixed
from app.services.wallet_auth.auth_intent import hash_intent
from app.services.wallet_auth.privacy_commitments import redact_sensitive_auth_material
from app.schemas.hardware_wallet import HardwareWalletClaim, VerifiedHardwareWalletEvidence

HARDWARE_EVIDENCE_TYPE = "bastion_hardware_wallet_evidence"
HARDWARE_EVIDENCE_VERSION = 1
HARDWARE_EVIDENCE_VERIFIER_ID = "bastion.hardware-evidence"
HARDWARE_EVIDENCE_VERIFIER_VERSION = "1"


@dataclass(frozen=True, slots=True)
class HardwareEvidenceContext:
    principal_hash: str
    device_key_fingerprint: str
    proof_method: str
    proof_reference_hash: str
    structured_intent: Mapping[str, object]
    origin: str
    domain: str
    requested_action: str
    risk_level: str
    policy_epoch: str
    now: datetime
    auth_domain: str | None = None
    k1_hash: str | None = None
    certificate_fingerprint: str | None = None
    recovery_attempt_hash: str | None = None

    @property
    def intent_hash(self) -> str:
        return hash_intent(self.structured_intent)


@dataclass(frozen=True, slots=True)
class IntentDisplayCoverage:
    intent_display_state: HardwareWalletIntentDisplayState
    meaningful_for_action: bool
    missing_fields: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


class HardwareEvidenceVerifier(Protocol):
    def supports(self, claim: HardwareWalletClaim) -> bool: ...

    def verify(self, claim: HardwareWalletClaim, context: HardwareEvidenceContext) -> VerifiedHardwareWalletEvidence: ...

    def verifier_id(self) -> str: ...

    def verifier_version(self) -> str: ...


def canonical_hardware_evidence_envelope(envelope: Mapping[str, object]) -> str:
    return canonical_json(envelope)


def hardware_evidence_fingerprint(envelope: Mapping[str, object]) -> str:
    return sha256_prefixed(canonical_hardware_evidence_envelope(envelope))


def build_hardware_evidence_envelope(
    *,
    context: HardwareEvidenceContext,
    claim: HardwareWalletClaim,
    evidence_status: HardwareWalletEvidenceStatus,
    effective_assurance: HardwareWalletAssuranceLevel,
    wallet_family: str,
    limitations: tuple[str, ...],
    issued_at: datetime,
    expires_at: datetime | None,
    verifier_id: str = HARDWARE_EVIDENCE_VERIFIER_ID,
    verifier_version: str = HARDWARE_EVIDENCE_VERIFIER_VERSION,
) -> dict[str, object]:
    return {
        "type": HARDWARE_EVIDENCE_TYPE,
        "version": HARDWARE_EVIDENCE_VERSION,
        "principal_hash": context.principal_hash,
        "device_key_fingerprint": context.device_key_fingerprint,
        "proof_method": context.proof_method,
        "proof_reference_hash": context.proof_reference_hash,
        "intent_hash": context.intent_hash,
        "wallet_family": wallet_family,
        "interaction_mode": claim.interaction_mode.value,
        "evidence_type": claim.evidence_type.value,
        "intent_display_state": claim.intent_display_state.value,
        "evidence_status": evidence_status.value,
        "effective_assurance": effective_assurance.value,
        "requested_action": context.requested_action,
        "origin": context.origin,
        "domain": context.domain,
        "policy_epoch": context.policy_epoch,
        "auth_domain": context.auth_domain,
        "k1_hash": context.k1_hash,
        "certificate_fingerprint": context.certificate_fingerprint,
        "recovery_attempt_hash": context.recovery_attempt_hash,
        "issued_at": issued_at.astimezone(UTC).isoformat(),
        "expires_at": expires_at.astimezone(UTC).isoformat() if expires_at else None,
        "verifier": {"id": verifier_id, "version": verifier_version},
        "limitations": list(limitations),
    }


def verified_evidence_from_envelope(
    *,
    envelope: Mapping[str, object],
    claim: HardwareWalletClaim,
    evidence_status: HardwareWalletEvidenceStatus,
    effective_assurance: HardwareWalletAssuranceLevel,
    wallet_family: str,
    limitations: tuple[str, ...],
    issued_at: datetime,
    expires_at: datetime | None,
    verifier_id: str,
    verifier_version: str,
) -> VerifiedHardwareWalletEvidence:
    fingerprint = hardware_evidence_fingerprint(envelope)
    return VerifiedHardwareWalletEvidence(
        evidence_id=fingerprint,
        evidence_type=claim.evidence_type,
        evidence_status=evidence_status,
        effective_assurance=effective_assurance,
        wallet_family=wallet_family,
        interaction_mode=claim.interaction_mode,
        intent_display_state=claim.intent_display_state,
        device_binding_eligible=evidence_status in {HardwareWalletEvidenceStatus.VERIFIED, HardwareWalletEvidenceStatus.PARTIALLY_VERIFIED},
        step_up_eligible=effective_assurance in {
            HardwareWalletAssuranceLevel.HARDWARE_ASSISTED,
            HardwareWalletAssuranceLevel.HARDWARE_VERIFIED,
            HardwareWalletAssuranceLevel.AIR_GAPPED,
            HardwareWalletAssuranceLevel.SOVEREIGN,
        },
        recovery_factor_eligible=effective_assurance in {HardwareWalletAssuranceLevel.HARDWARE_VERIFIED, HardwareWalletAssuranceLevel.AIR_GAPPED},
        sovereign_quorum_eligible=effective_assurance is HardwareWalletAssuranceLevel.SOVEREIGN,
        limitations=limitations,
        evidence_fingerprint=fingerprint,
        issued_at=issued_at,
        expires_at=expires_at,
        verifier_id=verifier_id,
        verifier_version=verifier_version,
    )


class NoEvidenceVerifier:
    def supports(self, claim: HardwareWalletClaim) -> bool:
        return claim.evidence_type is HardwareWalletEvidenceType.NONE

    def verifier_id(self) -> str:
        return "bastion.hardware.no-evidence"

    def verifier_version(self) -> str:
        return "1"

    def verify(self, claim: HardwareWalletClaim, context: HardwareEvidenceContext) -> VerifiedHardwareWalletEvidence:
        issued_at = context.now.astimezone(UTC)
        limitations = ("no_hardware_evidence_present", "hardware_claim_does_not_authorize_access")
        envelope = build_hardware_evidence_envelope(
            context=context,
            claim=claim,
            evidence_status=HardwareWalletEvidenceStatus.ABSENT,
            effective_assurance=HardwareWalletAssuranceLevel.UNKNOWN,
            wallet_family="unknown",
            limitations=limitations,
            issued_at=issued_at,
            expires_at=None,
            verifier_id=self.verifier_id(),
            verifier_version=self.verifier_version(),
        )
        return verified_evidence_from_envelope(
            envelope=envelope,
            claim=claim,
            evidence_status=HardwareWalletEvidenceStatus.ABSENT,
            effective_assurance=HardwareWalletAssuranceLevel.UNKNOWN,
            wallet_family="unknown",
            limitations=limitations,
            issued_at=issued_at,
            expires_at=None,
            verifier_id=self.verifier_id(),
            verifier_version=self.verifier_version(),
        )


class SelfClaimedHardwareVerifier:
    def supports(self, claim: HardwareWalletClaim) -> bool:
        return claim.evidence_type in {HardwareWalletEvidenceType.SELF_CLAIMED, HardwareWalletEvidenceType.WALLET_SOFTWARE_REPORT}

    def verifier_id(self) -> str:
        return "bastion.hardware.self-claimed"

    def verifier_version(self) -> str:
        return "1"

    def verify(self, claim: HardwareWalletClaim, context: HardwareEvidenceContext) -> VerifiedHardwareWalletEvidence:
        issued_at = context.now.astimezone(UTC)
        expires_at = issued_at + timedelta(hours=24)
        limitations = (
            "client_claim_not_hardware_proof",
            "does_not_satisfy_recovery_enterprise_sovereign_or_treasury_policy",
        )
        envelope = build_hardware_evidence_envelope(
            context=context,
            claim=claim,
            evidence_status=HardwareWalletEvidenceStatus.UNVERIFIED,
            effective_assurance=HardwareWalletAssuranceLevel.CLAIMED,
            wallet_family=_wallet_family(claim),
            limitations=limitations,
            issued_at=issued_at,
            expires_at=expires_at,
            verifier_id=self.verifier_id(),
            verifier_version=self.verifier_version(),
        )
        return verified_evidence_from_envelope(
            envelope=envelope,
            claim=claim,
            evidence_status=HardwareWalletEvidenceStatus.UNVERIFIED,
            effective_assurance=HardwareWalletAssuranceLevel.CLAIMED,
            wallet_family=_wallet_family(claim),
            limitations=limitations,
            issued_at=issued_at,
            expires_at=expires_at,
            verifier_id=self.verifier_id(),
            verifier_version=self.verifier_version(),
        )


class DeviceDisplayEvidenceVerifier:
    def supports(self, claim: HardwareWalletClaim) -> bool:
        return claim.evidence_type is HardwareWalletEvidenceType.DEVICE_DISPLAY_CONFIRMATION

    def verifier_id(self) -> str:
        return "bastion.hardware.display-evidence"

    def verifier_version(self) -> str:
        return "1"

    def verify(self, claim: HardwareWalletClaim, context: HardwareEvidenceContext) -> VerifiedHardwareWalletEvidence:
        coverage = evaluate_intent_display_coverage(context.structured_intent, claim.metadata)
        issued_at = context.now.astimezone(UTC)
        expires_at = min(
            claim.evidence_expires_at.astimezone(UTC) if claim.evidence_expires_at else issued_at + timedelta(minutes=5),
            issued_at + timedelta(minutes=5),
        )
        status = HardwareWalletEvidenceStatus.VERIFIED if coverage.meaningful_for_action else HardwareWalletEvidenceStatus.PARTIALLY_VERIFIED
        assurance = HardwareWalletAssuranceLevel.HARDWARE_ASSISTED if coverage.meaningful_for_action else HardwareWalletAssuranceLevel.CLAIMED
        limitations = coverage.limitations or ("device_display_evidence_limited_to_intent_coverage",)
        envelope = build_hardware_evidence_envelope(
            context=context,
            claim=claim,
            evidence_status=status,
            effective_assurance=assurance,
            wallet_family=_wallet_family(claim),
            limitations=limitations,
            issued_at=issued_at,
            expires_at=expires_at,
            verifier_id=self.verifier_id(),
            verifier_version=self.verifier_version(),
        )
        return verified_evidence_from_envelope(
            envelope=envelope,
            claim=claim,
            evidence_status=status,
            effective_assurance=assurance,
            wallet_family=_wallet_family(claim),
            limitations=limitations,
            issued_at=issued_at,
            expires_at=expires_at,
            verifier_id=self.verifier_id(),
            verifier_version=self.verifier_version(),
        )


class VendorAttestationVerifier(NoEvidenceVerifier):
    def supports(self, claim: HardwareWalletClaim) -> bool:
        return claim.evidence_type in {
            HardwareWalletEvidenceType.VENDOR_ATTESTATION,
            HardwareWalletEvidenceType.SECURE_ELEMENT_ATTESTATION,
            HardwareWalletEvidenceType.TRUSTED_EXECUTION_ATTESTATION,
        }

    def verifier_id(self) -> str:
        return "bastion.hardware.vendor-attestation-extension"

    def verify(self, claim: HardwareWalletClaim, context: HardwareEvidenceContext) -> VerifiedHardwareWalletEvidence:
        result = super().verify(claim, context)
        return result.model_copy(
            update={
                "evidence_type": claim.evidence_type,
                "evidence_status": HardwareWalletEvidenceStatus.UNSUPPORTED,
                "limitations": ("vendor_trust_root_not_configured", "fake_vendor_attestation_forbidden"),
            }
        )


class AirGappedArtifactVerifier(NoEvidenceVerifier):
    def supports(self, claim: HardwareWalletClaim) -> bool:
        return claim.evidence_type is HardwareWalletEvidenceType.AIR_GAPPED_ARTIFACT

    def verifier_id(self) -> str:
        return "bastion.hardware.air-gapped-artifact-extension"

    def verify(self, claim: HardwareWalletClaim, context: HardwareEvidenceContext) -> VerifiedHardwareWalletEvidence:
        result = super().verify(claim, context)
        return result.model_copy(
            update={
                "evidence_type": claim.evidence_type,
                "evidence_status": HardwareWalletEvidenceStatus.UNSUPPORTED,
                "limitations": ("air_gapped_artifact_policy_not_configured", "air_gap_claim_alone_not_assurance"),
            }
        )


def evaluate_intent_display_coverage(intent: Mapping[str, object], hardware_display_evidence: Mapping[str, object]) -> IntentDisplayCoverage:
    displayed_value = hardware_display_evidence.get("displayed_fields", ())
    if isinstance(displayed_value, (list, tuple, set)):
        displayed = {str(item) for item in displayed_value}
    else:
        displayed = set()
    action = str(intent.get("action", ""))
    high_risk = str(intent.get("risk_level", "low")).lower() in {"high", "critical", "sovereign"}
    required = {"domain", "action", "expires_at", "warnings"}
    if high_risk:
        required.update({"requested_scopes", "risk_level", "policy_hash"})
    missing = tuple(sorted(required - displayed))
    if not displayed:
        return IntentDisplayCoverage(
            HardwareWalletIntentDisplayState.NOT_DISPLAYED,
            False,
            tuple(sorted(required)),
            ("browser_or_companion_display_only_is_not_hardware_evidence",),
        )
    if missing:
        return IntentDisplayCoverage(
            HardwareWalletIntentDisplayState.PARTIALLY_DISPLAYED,
            False,
            missing,
            ("hardware_intent_display_incomplete", f"action={redact_sensitive_auth_material(action)}"),
        )
    return IntentDisplayCoverage(
        HardwareWalletIntentDisplayState.FULLY_DISPLAYED,
        True,
        (),
        ("no_vendor_secure_element_attestation_available",),
    )


def _wallet_family(claim: HardwareWalletClaim) -> str:
    family = claim.metadata.get("wallet_family") if isinstance(claim.metadata, dict) else None
    if isinstance(family, str) and family.strip():
        return family.strip().lower().replace(" ", "_")
    if claim.vendor_name:
        return claim.vendor_name.strip().lower().replace(" ", "_")
    return "generic_hardware_wallet"


def dataclass_to_log_safe_dict(value: object) -> dict[str, object]:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        raw = dataclasses.asdict(value)
    elif isinstance(value, Mapping):
        raw = dict(value)
    else:
        raw = {"value": str(value)}
    return {key: redact_sensitive_auth_material(str(item)) for key, item in raw.items()}
