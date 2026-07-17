from __future__ import annotations

from bastion_ui.security.safety_copy import TRACE_PUBLIC_SAFETY_COPY


def test_trace_required_safety_copy_visible() -> None:
    for phrase in (
        "Advisory-only.",
        "Not legal verification.",
        "Not Bitcoin consensus proof.",
        "No custody.",
        "Public Bitcoin addresses only.",
        "Never enter seed phrases, private keys, wallet files or signing material.",
    ):
        assert phrase in TRACE_PUBLIC_SAFETY_COPY
