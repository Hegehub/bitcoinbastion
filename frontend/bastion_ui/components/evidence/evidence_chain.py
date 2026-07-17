from __future__ import annotations

from typing import Any

import reflex as rx

from bastion_ui.components.evidence.evidence_card import evidence_card
from bastion_ui.components.ui.card import card
from bastion_ui.components.ui.empty_state import empty_state


def evidence_chain(items: list[dict[str, Any]] | None = None) -> rx.Component:
    evidence_items = items or []
    if not evidence_items:
        return empty_state(
            "No evidence items loaded",
            "Cryptographic verification is not available in this frontend view.",
        )
    return card(
        *[evidence_card(item) for item in evidence_items],
        rx.text("Cryptographic verification is not available in this frontend view."),
        title="Evidence chain",
        variant="evidence",
    )
