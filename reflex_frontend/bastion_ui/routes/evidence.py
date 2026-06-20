from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.public.evidence_overview import evidence_overview
from bastion_ui.routes._shared import link_card, public_page


def evidence_page() -> rx.Component:
    return public_page(
        "Evidence",
        evidence_overview(),
        responsive_grid(
            link_card("Trace", "/trace", "Trace will link evidence to reports in a later prompt."),
            link_card(
                "Status", "/status", "Provider and backend status affects evidence confidence."
            ),
        ),
        subtitle="Evidence packets, audit trails, replay concepts, and limitations.",
    )
