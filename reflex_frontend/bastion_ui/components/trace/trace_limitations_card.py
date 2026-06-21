from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import two_column_grid
from bastion_ui.components.ui.card import card

TRACE_CAN_PROVIDE = (
    "source-based context",
    "provider disagreement",
    "privacy exposure indicators",
    "evidence-linked advisory review",
    "manual review hints",
)
TRACE_CANNOT_PROVIDE = (
    "legal judgment",
    "guarantee of safety",
    "criminal attribution",
    "Bitcoin consensus proof",
    "custody or transaction signing",
)


def trace_limitations_card() -> rx.Component:
    return card(
        two_column_grid(
            card(*[rx.text(f"• {item}") for item in TRACE_CAN_PROVIDE], title="Trace can provide"),
            card(
                *[rx.text(f"• {item}") for item in TRACE_CANNOT_PROVIDE],
                title="Trace cannot provide",
            ),
        ),
        title="Trace limitations",
        variant="safety",
    )
