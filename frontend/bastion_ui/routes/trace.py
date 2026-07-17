from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.public.pillar_card import pillar_card
from bastion_ui.components.trace.public_flow import trace_public_flow
from bastion_ui.routes._shared import link_card, public_page


def trace_page() -> rx.Component:
    return public_page(
        "Bastion Trace",
        rx.text(
            "A public-address intelligence layer for Bitcoin risk context, source disagreement, "
            "privacy exposure, and evidence-based review."
        ),
        rx.text(
            "Trace is advisory-only. It does not custody funds, does not sign transactions, "
            "does not prove legal status, and does not produce Bitcoin consensus proofs."
        ),
        trace_public_flow(),
        responsive_grid(
            pillar_card("Source context", "Trace can show source-based context.", "baseline"),
            pillar_card(
                "Provider disagreement", "Trace can highlight source disagreement.", "baseline"
            ),
            pillar_card(
                "Privacy exposure", "Trace can surface advisory privacy indicators.", "baseline"
            ),
            pillar_card(
                "Evidence review", "Trace can connect findings to evidence review.", "planned"
            ),
            pillar_card("No legal judgment", "Trace cannot prove legal status.", "implemented"),
            pillar_card(
                "No signing", "Trace does not custody funds or sign transactions.", "implemented"
            ),
        ),
        responsive_grid(
            link_card("Evidence", "/evidence", "Review Evidence concepts."),
            link_card("Status", "/status", "Check backend/provider status posture."),
            link_card("Docs", "/docs", "Open public documentation."),
        ),
        subtitle="Public Trace landing page and Trace Lite entrypoint.",
    )
