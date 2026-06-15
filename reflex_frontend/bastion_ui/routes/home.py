from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.layout.public_layout import public_layout
from bastion_ui.components.ui.button import button
from bastion_ui.components.ui.card import card
from bastion_ui.components.ui.safety_banner import advisory_banner, degraded_state_banner, no_custody_banner


def home_page() -> rx.Component:
    """Render the public Reflex home route."""

    return public_layout(cast(rx.Component, rx.vstack(
        rx.badge("Experimental Reflex frontend shell.", color_scheme="orange", size="2"),
        rx.heading("Bitcoin-first sovereign backend for evidence-driven intelligence and operations.", size="8"),
        rx.text("Bitcoin Bastion is a no-custody, advisory-only, evidence-oriented system. FastAPI remains the source of truth. FastAPI remains authoritative for backend data and decisions."),
        rx.text("No custody."),
        rx.text("Never enter seed phrases, private keys, wallet files or signing material."),
        rx.text("Advisory-only."),
        no_custody_banner(),
        advisory_banner(),
        degraded_state_banner(),
        rx.hstack(
            button("Platform", "/platform"),
            button("Trace", "/trace", "secondary"),
            button("Evidence", "/evidence", "secondary"),
            button("Status", "/status", "secondary"),
            button("Developers", "/developers", "ghost"),
            button("Operations", "/operations", "ghost"),
            wrap="wrap",
        ),
        rx.grid(
            card(rx.text("Bitcoin-first posture with explicit no-custody boundaries."), title="Bitcoin-first"),
            card(rx.text("Evidence packets, replay, provider health, and deployment evidence guide operator trust."), title="Evidence-oriented backend"),
            card(rx.text("Reflex runs in parallel. Next.js remains available until route and API parity are proven."), title="Parallel frontend"),
            card(rx.text("The existing FastAPI/Jinja Market dashboard keeps ownership of /market for now."), title="No /market migration"),
            columns="2",
            spacing="4",
            width="100%",
        ),
        spacing="5",
        align="start",
        width="100%",
    )))
