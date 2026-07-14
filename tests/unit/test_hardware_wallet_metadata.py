from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.wallet_auth.hardware import (
    HardwareWalletAssuranceLevel,
    HardwareWalletEvidenceStatus,
    HardwareWalletEvidenceType,
    HardwareWalletIntentDisplayState,
    HardwareWalletInteractionMode,
)
from app.schemas.hardware_wallet import HardwareWalletClaim, hash_serial_number
from app.services.wallet_auth.hardware_evidence import (
    HardwareEvidenceContext,
    build_hardware_evidence_envelope,
    hardware_evidence_fingerprint,
)


def claim(**kwargs) -> HardwareWalletClaim:
    data = {
        "wallet_name": "Test Wallet",
        "vendor_name": "Generic Vendor",
        "device_model": "Model A",
        "interaction_mode": HardwareWalletInteractionMode.QR,
        "evidence_type": HardwareWalletEvidenceType.DEVICE_DISPLAY_CONFIRMATION,
        "evidence_status": HardwareWalletEvidenceStatus.UNVERIFIED,
        "intent_display_state": HardwareWalletIntentDisplayState.FULLY_DISPLAYED,
        "proof_method": "bip322",
        "metadata": {"wallet_family": "generic_hardware_wallet", "displayed_fields": ["domain", "action", "expires_at", "warnings"]},
    }
    data.update(kwargs)
    return HardwareWalletClaim(**data)


def context(action: str = "login") -> HardwareEvidenceContext:
    now = datetime(2026, 7, 13, 12, tzinfo=UTC)
    return HardwareEvidenceContext(
        principal_hash="hmac-sha256:" + "a" * 64,
        device_key_fingerprint="sha256:" + "b" * 64,
        proof_method="bip322",
        proof_reference_hash="sha256:" + "c" * 64,
        structured_intent={"domain": "auth.bitcoin-bastion.com", "action": action, "expires_at": (now + timedelta(minutes=5)).isoformat(), "warnings": ["safe"]},
        origin="https://auth.bitcoin-bastion.com",
        domain="auth.bitcoin-bastion.com",
        requested_action=action,
        risk_level="low",
        policy_epoch="policy-1",
        now=now,
    )


def test_schema_accepts_safe_metadata_and_serial_is_hashed():
    safe = claim()
    assert safe.wallet_name == "Test Wallet"
    hashed = hash_serial_number("test-serial-123")
    assert hashed.startswith("sha256:")
    assert "test-serial-123" not in hashed


@pytest.mark.parametrize("field,value", [("metadata", {"seed": "secret"}), ("metadata", {"nested": {"mnemonic": "words"}}), ("vendor_name", "xprv secret"), ("metadata", {"private_key": "abc"})])
def test_schema_rejects_secret_material(field: str, value: object):
    with pytest.raises(ValueError):
        claim(**{field: value})


def test_self_claim_cannot_mark_itself_verified():
    with pytest.raises(ValueError):
        claim(evidence_type=HardwareWalletEvidenceType.SELF_CLAIMED, evidence_status=HardwareWalletEvidenceStatus.VERIFIED)


def test_canonical_evidence_fingerprint_is_stable_and_tamper_sensitive():
    ctx = context()
    hw_claim = claim()
    issued = ctx.now
    envelope = build_hardware_evidence_envelope(
        context=ctx,
        claim=hw_claim,
        evidence_status=HardwareWalletEvidenceStatus.VERIFIED,
        effective_assurance=HardwareWalletAssuranceLevel.HARDWARE_ASSISTED,
        wallet_family="generic_hardware_wallet",
        limitations=("No vendor secure-element attestation was available.",),
        issued_at=issued,
        expires_at=issued + timedelta(minutes=5),
    )
    fingerprint = hardware_evidence_fingerprint(envelope)
    assert fingerprint == hardware_evidence_fingerprint(dict(reversed(list(envelope.items()))))
    tampered = dict(envelope)
    tampered["requested_action"] = "treasury_policy_change"
    assert hardware_evidence_fingerprint(tampered) != fingerprint
