from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.layout.section import section
from bastion_ui.components.public.feature_grid import feature_grid
from bastion_ui.components.public.hero import public_hero
from bastion_ui.components.ui.card import card
from bastion_ui.routes._public import public_page

DEVELOPER_AREAS = (
    ("Public API", "Landing, status, roadmap, stats, and features endpoints.", "baseline"),
    ("Event Bus", "Backend implementation must be confirmed before UI claims.", "experimental"),
    ("Webhooks", "Webhook docs are pending stable contract confirmation.", "planned"),
    ("WebSocket", "Realtime transport is documented only after backend parity.", "planned"),
    (
        "Python SDK",
        "SDK status is treated as preview until package release is verified.",
        "planned",
    ),
    ("CLI", "CLI references are conservative until commands are audited.", "planned"),
    ("MCP connector", "Connector support remains experimental unless validated.", "experimental"),
)


def developers_page() -> rx.Component:
    return public_page(
        public_hero(
            "API-first Bitcoin Bastion development",
            "Build against backend contracts, safe response envelopes, and explicit degraded "
            "states. Reflex does not duplicate backend domain logic.",
            primary_label="Open API contract",
            primary_href="/docs",
            secondary_label="View Status",
            secondary_href="/status",
        ),
        section(feature_grid(DEVELOPER_AREAS), title="Developer surface status"),
        section(
            responsive_grid(
                card(
                    rx.text("Docs landing and API contract references."),
                    title="Docs",
                    badge=rx.badge("baseline"),
                ),
                card(
                    rx.text("Backend health and degraded visibility."),
                    title="Status",
                    badge=rx.badge("baseline"),
                ),
                card(
                    rx.text("Migration sequence and known blockers."),
                    title="Roadmap",
                    badge=rx.badge("baseline"),
                ),
            ),
            title="Developer links",
        ),
    )
