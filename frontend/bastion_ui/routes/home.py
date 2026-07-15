from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.public.hero import public_hero
from bastion_ui.components.public.pillar_card import pillar_card
from bastion_ui.components.public.roadmap_preview import roadmap_preview
from bastion_ui.components.public.status_summary import status_fallback_card
from bastion_ui.routes._shared import link_card, public_page


def home_page() -> rx.Component:
    return public_page(
        "Sovereign Bitcoin Intelligence Backend",
        public_hero(
            "Bitcoin Bastion",
            "Bitcoin-first public migration route",
            "No-custody, evidence-over-claims infrastructure for operators who need "
            "local-first visibility, transparent degraded states, and rollback discipline.",
        ),
        responsive_grid(
            pillar_card(
                "Trace",
                "Advisory address and report workflows remain visible; full Trace "
                "migration follows later.",
                "planned",
            ),
            pillar_card(
                "Evidence",
                "Evidence packets and review trails explain source-dependent reasoning.",
                "baseline",
            ),
            pillar_card(
                "Market Intelligence",
                "Market dashboard remains FastAPI/Jinja-owned until Reflex parity is proven.",
                "planned",
            ),
            pillar_card(
                "Developer API Layer",
                "FastAPI remains the source of truth for public, Trace, status, and roadmap data.",
                "baseline",
            ),
            pillar_card(
                "Runtime Profiles",
                "Docker, Kubernetes, k3s, kind, minikube, single-node, and "
                "bare-metal paths are tracked conservatively.",
                "baseline",
            ),
            pillar_card(
                "Operator Control",
                "Risky workflows require human review and must not execute automatically.",
                "baseline",
            ),
        ),
        responsive_grid(
            link_card(
                "Open Trace",
                "/trace",
                "Trace remains first-class, with full workflow migration deferred.",
            ),
            link_card(
                "Developer API",
                "/developers",
                "Review API-first integration points and endpoint readiness.",
            ),
            link_card(
                "Operations", "/operations", "Review self-hosting and runtime profile posture."
            ),
        ),
        status_fallback_card(),
        roadmap_preview(),
        subtitle="Reflex public route; not a production-readiness claim.",
    )
