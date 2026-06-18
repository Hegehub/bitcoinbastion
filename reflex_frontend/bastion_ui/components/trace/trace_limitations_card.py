from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
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
    "guarantee of payment outcome",
    "attribution of wrongdoing",
    "Bitcoin consensus proof",
    "custody or transaction signing",
)
TRACE_REPORT_LIMITATIONS = (
    "This report is advisory-only.",
    "It is not legal verification.",
    "It is not a Bitcoin consensus proof.",
    "It may be incomplete.",
    "Providers may disagree.",
    "Data may be stale or unavailable.",
    "Manual review may be required.",
)


def _items(items: tuple[str, ...]) -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(*[rx.text(f"• {item}") for item in items], align="start", spacing="2"),
    )


def trace_limitations_card() -> rx.Component:
    return card(
        responsive_grid(
            card(_items(TRACE_CAN_PROVIDE), title="Trace can provide"),
            card(_items(TRACE_CANNOT_PROVIDE), title="Trace cannot provide"),
            card(_items(TRACE_REPORT_LIMITATIONS), title="Report limitations"),
        ),
        title="Trace limitations",
        subtitle="Trace is advisory context, not a verdict or proof system.",
        variant="safety",
    )
