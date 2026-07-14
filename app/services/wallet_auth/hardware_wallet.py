"""Facade helpers for hardware-wallet metadata evaluation."""

from __future__ import annotations

from app.services.wallet_auth.hardware_assurance import HardwareAssuranceEvaluator
from app.services.wallet_auth.hardware_evidence import (
    AirGappedArtifactVerifier,
    DeviceDisplayEvidenceVerifier,
    NoEvidenceVerifier,
    SelfClaimedHardwareVerifier,
    VendorAttestationVerifier,
)


def build_default_hardware_assurance_evaluator() -> HardwareAssuranceEvaluator:
    return HardwareAssuranceEvaluator(
        (
            NoEvidenceVerifier(),
            SelfClaimedHardwareVerifier(),
            DeviceDisplayEvidenceVerifier(),
            VendorAttestationVerifier(),
            AirGappedArtifactVerifier(),
        )
    )
