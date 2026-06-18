from __future__ import annotations

from bastion_ui.components.trace.trace_limitations_card import (
    TRACE_CAN_PROVIDE,
    TRACE_CANNOT_PROVIDE,
)
from bastion_ui.components.trace.trace_safety_banner import TRACE_SAFETY_COPY


def test_trace_safety_copy_contains_required_phrases() -> None:
    assert "Advisory-only." in TRACE_SAFETY_COPY
    assert "Not legal verification." in TRACE_SAFETY_COPY
    assert "Not Bitcoin consensus proof." in TRACE_SAFETY_COPY
    assert "No custody." in TRACE_SAFETY_COPY
    assert "Public Bitcoin addresses only." in TRACE_SAFETY_COPY
    assert "Never enter seed phrases, private keys, wallet files or signing material." in (
        TRACE_SAFETY_COPY
    )


def test_trace_limitations_are_explicit() -> None:
    assert "source-based context" in TRACE_CAN_PROVIDE
    assert "provider disagreement" in TRACE_CAN_PROVIDE
    assert "Bitcoin consensus proof" in TRACE_CANNOT_PROVIDE
    assert "custody or transaction signing" in TRACE_CANNOT_PROVIDE
