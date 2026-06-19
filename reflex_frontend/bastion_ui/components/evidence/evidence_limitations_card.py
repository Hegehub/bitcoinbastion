from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.ui.card import card

EVIDENCE_LIMITATIONS = (
    "Trace is advisory-only.",
    "Trace depends on available data sources.",
    "Provider data may be stale or incomplete.",
    "Address clustering can be uncertain.",
    "Risk bands are not legal labels.",
    "A report is not a Bitcoin consensus proof.",
    "A report is not financial advice.",
    "Operators must review high-impact decisions manually.",
)


def evidence_limitations_card() -> rx.Component:
    return card(
        cast(
            rx.Component,
            rx.vstack(*[rx.text(f"• {item}") for item in EVIDENCE_LIMITATIONS], align="start"),
        ),
        title="Evidence and Trace limitations",
        subtitle="Evidence supports operator review; it does not replace human judgment.",
        variant="safety",
    )
