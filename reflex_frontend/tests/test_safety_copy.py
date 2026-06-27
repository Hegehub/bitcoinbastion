from __future__ import annotations

from bastion_ui.security import safety_copy


def test_required_safety_copy_exists() -> None:
    assert safety_copy.ADVISORY_ONLY
    assert safety_copy.NOT_LEGAL_VERIFICATION
    assert safety_copy.NOT_CONSENSUS_PROOF
    assert safety_copy.NO_CUSTODY
    assert safety_copy.PUBLIC_ADDRESSES_ONLY
    assert safety_copy.NEVER_ENTER_SENSITIVE_MATERIAL
    assert "public Bitcoin addresses only" in safety_copy.SENSITIVE_INPUT_ERROR
