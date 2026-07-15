from __future__ import annotations

import pytest

pytest.importorskip("reflex")

from bastion_ui.components.public.evidence_overview import EVIDENCE_LIMITATIONS_COPY
from bastion_ui.components.public.safety_section import REQUIRED_SAFETY_COPY, SECURITY_WARNING


def test_required_public_safety_copy_is_present() -> None:
    for phrase in (
        "Advisory-only.",
        "Not legal verification.",
        "Not Bitcoin consensus proof.",
        "No custody.",
        "Public Bitcoin addresses only.",
        "Never enter seed phrases, private keys, wallet files or signing material.",
    ):
        assert phrase in REQUIRED_SAFETY_COPY


def test_evidence_and_security_copy_include_limitations() -> None:
    assert "Evidence is not legal verification." in EVIDENCE_LIMITATIONS_COPY
    assert "Evidence is not Bitcoin consensus proof." in EVIDENCE_LIMITATIONS_COPY
    assert "Evidence is advisory and source-dependent." in EVIDENCE_LIMITATIONS_COPY
    assert "Never enter seed phrases, private keys, wallet files" in SECURITY_WARNING
    assert "xprv, yprv, zprv" in SECURITY_WARNING
