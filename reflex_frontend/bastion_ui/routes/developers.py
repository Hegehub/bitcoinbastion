from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.public.pillar_card import pillar_card
from bastion_ui.routes._shared import link_card, public_page


def developers_page() -> rx.Component:
    return public_page(
        "Developers",
        responsive_grid(
            pillar_card(
                "API-first",
                "FastAPI remains the integration boundary for Reflex and external clients.",
                "implemented",
            ),
            pillar_card(
                "Event Bus",
                "Event-driven architecture is tracked for integration work.",
                "baseline",
            ),
            pillar_card(
                "Webhooks",
                "Webhook endpoints exist but docs and parity validation are pending.",
                "experimental",
            ),
            pillar_card(
                "WebSocket",
                "Realtime interfaces need follow-up validation before public docs "
                "claim completeness.",
                "experimental",
            ),
            pillar_card(
                "Python SDK",
                "SDK surface is not claimed complete in this migration step.",
                "planned",
            ),
            pillar_card(
                "CLI", "CLI posture is documented conservatively until verified.", "planned"
            ),
            pillar_card(
                "MCP connector", "Connector integration remains a preview/planned area.", "planned"
            ),
            pillar_card(
                "Public endpoints",
                "Landing, status, roadmap, stats, features, and Trace summary clients exist.",
                "baseline",
            ),
        ),
        responsive_grid(
            link_card("Docs", "/docs", "Open the documentation landing page."),
            link_card("Status", "/status", "Review backend health fallback and status posture."),
            link_card("Roadmap", "/roadmap", "Review migration sequencing and blockers."),
        ),
        subtitle="Developer/API layer with conservative implementation labels.",
    )
