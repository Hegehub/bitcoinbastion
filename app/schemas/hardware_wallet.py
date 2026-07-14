"""Schemas for hardware-wallet metadata and normalized evidence."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.domain.wallet_auth.hardware import (
    HardwareWalletAssuranceLevel,
    HardwareWalletEvidenceStatus,
    HardwareWalletEvidenceType,
    HardwareWalletIntentDisplayState,
    HardwareWalletInteractionMode,
)
from app.services.wallet_auth.privacy_commitments import compute_sha256_commitment, reject_forbidden_wallet_secret_input

_SECRET_KEYS = {
    "seed",
    "mnemonic",
    "private_key",
    "xprv",
    "raw_proof",
    "proof",
    "wallet_address",
    "signature",
    "attestation_blob",
    "serial_number",
    "recovery_material",
    "k1",
    "linking_key",
    "session_token",
    "access_pass",
}


class HardwareWalletSchemaBase(BaseModel):
    model_config = {"extra": "forbid", "use_enum_values": False}


def _reject_secret_value(value: Any, field_name: str) -> None:
    if isinstance(value, str):
        reject_forbidden_wallet_secret_input(value, field_name)
    elif isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key).lower()
            if key_text in _SECRET_KEYS or any(secret in key_text for secret in _SECRET_KEYS):
                raise ValueError("hardware wallet metadata contains forbidden secret material")
            _reject_secret_value(item, key_text)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            _reject_secret_value(item, field_name)


class HardwareWalletClaim(HardwareWalletSchemaBase):
    version: int = Field(default=1, ge=1)
    wallet_name: str | None = None
    wallet_version: str | None = None
    vendor_name: str | None = None
    device_model: str | None = None
    firmware_version: str | None = None
    interaction_mode: HardwareWalletInteractionMode = HardwareWalletInteractionMode.UNKNOWN
    evidence_type: HardwareWalletEvidenceType = HardwareWalletEvidenceType.NONE
    evidence_status: HardwareWalletEvidenceStatus = HardwareWalletEvidenceStatus.UNVERIFIED
    intent_display_state: HardwareWalletIntentDisplayState = HardwareWalletIntentDisplayState.UNKNOWN
    requested_assurance: HardwareWalletAssuranceLevel | None = None
    device_key_fingerprint: str | None = None
    principal_hash: str | None = None
    proof_method: str = "unknown"
    proof_reference_hash: str | None = None
    attestation_reference_hash: str | None = None
    compatibility_record_id: str | None = None
    evidence_issued_at: datetime | None = None
    evidence_expires_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("wallet_name", "wallet_version", "vendor_name", "device_model", "firmware_version", "device_key_fingerprint", "principal_hash", "proof_method", "proof_reference_hash", "attestation_reference_hash", "compatibility_record_id")
    @classmethod
    def reject_secret_strings(cls, value: str | None) -> str | None:
        if value is not None:
            _reject_secret_value(value, "hardware_wallet_claim")
        return value

    @field_validator("metadata")
    @classmethod
    def reject_secret_metadata(cls, metadata: dict[str, Any]) -> dict[str, Any]:
        _reject_secret_value(metadata, "metadata")
        return metadata

    @model_validator(mode="after")
    def client_claims_remain_unverified(self) -> "HardwareWalletClaim":
        if self.evidence_type is HardwareWalletEvidenceType.SELF_CLAIMED and self.evidence_status is HardwareWalletEvidenceStatus.VERIFIED:
            raise ValueError("self-claimed hardware evidence cannot be marked verified by the client")
        if self.requested_assurance in {
            HardwareWalletAssuranceLevel.HARDWARE_VERIFIED,
            HardwareWalletAssuranceLevel.AIR_GAPPED,
            HardwareWalletAssuranceLevel.SOVEREIGN,
        } and self.evidence_status is not HardwareWalletEvidenceStatus.VERIFIED:
            # Accept the claim as a request, but force services to treat it as unverified metadata.
            object.__setattr__(self, "evidence_status", HardwareWalletEvidenceStatus.UNVERIFIED)
        return self


class VerifiedHardwareWalletEvidence(HardwareWalletSchemaBase):
    evidence_id: str
    evidence_type: HardwareWalletEvidenceType
    evidence_status: HardwareWalletEvidenceStatus
    effective_assurance: HardwareWalletAssuranceLevel
    wallet_family: str
    interaction_mode: HardwareWalletInteractionMode
    intent_display_state: HardwareWalletIntentDisplayState
    device_binding_eligible: bool
    step_up_eligible: bool
    recovery_factor_eligible: bool
    sovereign_quorum_eligible: bool
    limitations: tuple[str, ...] = ()
    evidence_fingerprint: str
    issued_at: datetime
    expires_at: datetime | None = None
    verifier_id: str
    verifier_version: str

    @field_validator("evidence_id", "wallet_family", "evidence_fingerprint", "verifier_id", "verifier_version")
    @classmethod
    def reject_secret_output_strings(cls, value: str) -> str:
        _reject_secret_value(value, "verified_hardware_evidence")
        return value


def hash_serial_number(serial_number: str, *, context: str = "hardware-wallet-serial") -> str:
    _reject_secret_value(serial_number, "serial_number")
    return compute_sha256_commitment(f"{context}:{serial_number.strip()}")
