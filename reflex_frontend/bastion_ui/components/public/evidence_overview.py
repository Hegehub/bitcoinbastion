from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.public.pillar_card import pillar_card
from bastion_ui.components.ui.alert import alert
from bastion_ui.components.ui.card import card

EVIDENCE_LIMITATIONS_COPY = (
    "Evidence is not legal verification. Evidence is not Bitcoin consensus proof. "
    "Evidence is advisory and source-dependent."
)


def evidence_overview() -> rx.Component:
    return card(
        alert(EVIDENCE_LIMITATIONS_COPY, "advisory"),
        responsive_grid(
            pillar_card("Evidence packets", "Explain source material and reasoning.", "baseline"),
            pillar_card("Audit trail", "Preserve review context for operators.", "planned"),
            pillar_card("Replay", "Replay concepts remain future route work.", "planned"),
            pillar_card("Provider disagreement", "Show when sources do not align.", "baseline"),
        ),
        title="Evidence overview",
    )
