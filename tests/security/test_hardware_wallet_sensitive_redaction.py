from __future__ import annotations

import pytest

from app.domain.wallet_auth.hardware import HardwareWalletEvidenceType
from app.schemas.hardware_wallet import HardwareWalletClaim
from app.services.wallet_auth.hardware_evidence import dataclass_to_log_safe_dict


@pytest.mark.parametrize(
    "payload",
    [
        {"signature": "raw-signature"},
        {"raw_proof": "raw-bip322-proof"},
        {"attestation_blob": "raw-attestation"},
        {"wallet_address": "bc1qqqqsyqcyq5rqwzqfpg9scrgwpugpzysn4v0345"},
        {"linking_key": "lnurl-linking-key"},
        {"k1": "f" * 64},
        {"serial_number": "serial-123"},
        {"seed": "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"},
        {"mnemonic": "seed words"},
        {"private_key": "xprv-secret"},
        {"xprv": "xprv-secret"},
    ],
)
def test_schema_rejects_sensitive_metadata(payload: dict[str, str]):
    with pytest.raises(ValueError):
        HardwareWalletClaim(evidence_type=HardwareWalletEvidenceType.SELF_CLAIMED, proof_method="bip322", metadata=payload)


def test_log_safe_dict_redacts_nested_sensitive_values():
    safe = dataclass_to_log_safe_dict({"signature": "raw-signature", "serial_number": "serial-123", "note": "ok"})
    assert "raw-signature" not in str(safe)
    assert "serial-123" not in str(safe)
