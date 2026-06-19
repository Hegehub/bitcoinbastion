from __future__ import annotations

from typing import Any, cast

import reflex as rx

from bastion_ui.components.evidence.evidence_card import evidence_card
from bastion_ui.components.ui.empty_state import empty_state

CRYPTOGRAPHIC_VERIFICATION_UNAVAILABLE = (
    "Cryptographic verification is not available in this frontend view."
)


def evidence_chain(items: list[dict[str, Any]] | None = None) -> rx.Component:
    evidence_items = items or []
    if not evidence_items:
        return empty_state(
            "No evidence items available",
            "Limited evidence. Provider did not return this field. "
            + CRYPTOGRAPHIC_VERIFICATION_UNAVAILABLE,
        )
    return cast(
        rx.Component,
        rx.vstack(
            rx.text(CRYPTOGRAPHIC_VERIFICATION_UNAVAILABLE),
            *[evidence_card(item) for item in evidence_items],
            align="stretch",
            spacing="4",
            width="100%",
        ),
    )
