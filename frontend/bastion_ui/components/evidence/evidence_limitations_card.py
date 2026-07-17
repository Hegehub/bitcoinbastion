from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card

EVIDENCE_LIMITATIONS = (
    "Evidence is advisory-only.",
    "Evidence is not legal verification.",
    "Evidence is not Bitcoin consensus proof.",
    "Evidence can be incomplete, stale, degraded, or provider-disputed.",
    "Evidence should support operator review, not replace it.",
    "Bitcoin Bastion does not custody funds.",
    "Never enter seed phrases, private keys, wallet files or signing material.",
)


def evidence_limitations_card() -> rx.Component:
    return card(
        *[rx.text(item) for item in EVIDENCE_LIMITATIONS],
        title="Evidence limitations",
        variant="safety",
    )
