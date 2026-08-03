# ruff: noqa: E501
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
                "Proof-of-Access API",
                "Protected clients use Authorization: PoP plus Bastion-Request-Timestamp, Bastion-Request-Nonce, Bastion-Request-Body-Hash, Bastion-Request-Signature, and Bastion-Principal. Legacy bearer authentication is disabled.",
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
                "SDK migration",
                "Python and TypeScript SDKs sign protected requests and redact Access Passes, sessions, signatures, and device material.",
                "implemented",
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
        subtitle="Developer/API layer for Proof-of-Access integrations; bearer auth is deprecated.",
    )
