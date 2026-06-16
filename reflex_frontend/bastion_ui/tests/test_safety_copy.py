from __future__ import annotations

from bastion_ui.components.safety.safety_banner import REQUIRED_SAFETY_COPY


def test_required_safety_copy_exists() -> None:
    assert "Advisory-only." in REQUIRED_SAFETY_COPY
    assert "Not legal verification." in REQUIRED_SAFETY_COPY
    assert "Not Bitcoin consensus proof." in REQUIRED_SAFETY_COPY
    assert "No custody." in REQUIRED_SAFETY_COPY
    assert "Public Bitcoin addresses only." in REQUIRED_SAFETY_COPY
    assert "Never enter seed phrases, private keys, wallet files or signing material." in (
        REQUIRED_SAFETY_COPY
    )
