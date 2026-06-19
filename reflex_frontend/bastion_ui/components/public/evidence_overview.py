from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.public.pillar_card import pillar_card
from bastion_ui.components.ui.alert import alert
from bastion_ui.components.ui.card import card

EVIDENCE_LIMITATIONS_COPY = (
    "Evidence is not legal verification. Evidence is not Bitcoin consensus proof. Evidence is "
    "advisory and source-dependent."
)


def evidence_overview() -> rx.Component:
    return card(
        alert(EVIDENCE_LIMITATIONS_COPY, "advisory"),
        responsive_grid(
            pillar_card(
                "Evidence packets",
                "Structured source material and system reasoning.",
                status="baseline",
            ),
            pillar_card(
                "Audit trail",
                "Operator-visible sequence of source and decision context.",
                status="planned",
            ),
            pillar_card(
                "Replay", "Future replay views should preserve source provenance.", status="planned"
            ),
            pillar_card(
                "Provider disagreement",
                "Surfaces disagreement instead of hiding uncertainty.",
                status="baseline",
            ),
        ),
        title="Evidence overview",
    )
