from __future__ import annotations

from bastion_ui.components.public.evidence_overview import EVIDENCE_LIMITATIONS_COPY
from bastion_ui.components.public.safety_section import (
    REQUIRED_PUBLIC_SAFETY_COPY,
    SECURITY_WARNING,
)
from bastion_ui.components.public.status_summary import STATUS_FALLBACK_COPY


def test_required_public_safety_copy_is_present() -> None:
    assert "Advisory-only." in REQUIRED_PUBLIC_SAFETY_COPY
    assert "Not legal verification." in REQUIRED_PUBLIC_SAFETY_COPY
    assert "Not Bitcoin consensus proof." in REQUIRED_PUBLIC_SAFETY_COPY
    assert "No custody." in REQUIRED_PUBLIC_SAFETY_COPY
    assert "Public Bitcoin addresses only." in REQUIRED_PUBLIC_SAFETY_COPY
    assert "Never enter seed phrases, private keys, wallet files or signing material." in (
        REQUIRED_PUBLIC_SAFETY_COPY
    )


def test_evidence_limitations_are_explicit() -> None:
    assert "Evidence is not legal verification." in EVIDENCE_LIMITATIONS_COPY
    assert "Evidence is not Bitcoin consensus proof." in EVIDENCE_LIMITATIONS_COPY
    assert "advisory and source-dependent" in EVIDENCE_LIMITATIONS_COPY


def test_security_warning_rejects_sensitive_wallet_material() -> None:
    assert "Never enter seed phrases" in SECURITY_WARNING
    assert "xprv, yprv, zprv" in SECURITY_WARNING
    assert "signing material" in SECURITY_WARNING


def test_status_page_has_safe_fallback_state() -> None:
    assert "Status temporarily unavailable." in STATUS_FALLBACK_COPY
    assert "cannot verify current backend health" in STATUS_FALLBACK_COPY
