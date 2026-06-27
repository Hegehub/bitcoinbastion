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
TRACE_REPORT_LIMITATIONS = (
    "This report is advisory-only.",
    "Trace depends on available data sources.",
    "Provider data may be stale or incomplete.",
    "Address clustering can be uncertain.",
    "Risk bands are not legal labels.",
    "It is not legal verification.",
    "It is not a Bitcoin consensus proof.",
    "A report is not financial advice.",
    "It may be incomplete.",
    "Providers may disagree.",
    "Data may be stale or unavailable.",
    "Manual review may be required.",
    "Operators must review high-impact decisions manually.",
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
        rx.vstack(*[rx.text(item) for item in TRACE_REPORT_LIMITATIONS], align="start"),
        title="Trace limitations",
        variant="safety",
    )
