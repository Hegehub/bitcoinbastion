from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.layout.section import section
from bastion_ui.components.public.feature_grid import feature_grid
from bastion_ui.components.public.hero import public_hero
from bastion_ui.components.public.roadmap_preview import roadmap_preview
from bastion_ui.components.public.safety_section import safety_section
from bastion_ui.components.public.status_summary import status_summary
from bastion_ui.components.ui.card import card
from bastion_ui.routes._public import public_page

HOME_PILLARS = (
    ("Trace", "Advisory address and report workflows remain backend-driven.", "planned"),
    ("Evidence", "Evidence packets favor source material over unsupported claims.", "baseline"),
    ("Market Intelligence", "Market and Time Machine stay delegated until parity.", "planned"),
    ("Developer API Layer", "Public API clients unwrap backend envelopes safely.", "baseline"),
    ("Runtime Profiles", "Self-hosting paths are documented with conservative status.", "baseline"),
    ("Operator Control", "Risky actions require human review and approval.", "baseline"),
)


def home_page() -> rx.Component:
    return public_page(
        public_hero(
            "Sovereign Bitcoin Intelligence Backend",
            "Bitcoin Bastion is Bitcoin-first infrastructure for advisory intelligence, "
            "evidence review, operator control, and transparent degraded states.",
            primary_label="Open Trace preview",
            primary_href="/trace",
            secondary_label="Developer API layer",
            secondary_href="/developers",
        ),
        section(
            feature_grid(HOME_PILLARS),
            title="Trace / Evidence / Market Intelligence",
        ),
        section(
            responsive_grid(
                card(
                    rx.text("No custody. No signing. No wallet-secret collection."),
                    title="No-custody safety model",
                ),
                card(
                    rx.text("Local-first and self-hostable deployment paths remain central."),
                    title="Runtime profiles",
                ),
                card(
                    rx.text("Status views must show degraded, fallback, and stale conditions."),
                    title="Status visibility",
                ),
            ),
            title="Operator-first posture",
        ),
        safety_section(),
        status_summary(),
        roadmap_preview(),
    )
