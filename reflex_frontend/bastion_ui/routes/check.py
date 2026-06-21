from __future__ import annotations

import reflex as rx

from bastion_ui.components.trace.public_flow import trace_public_flow
from bastion_ui.components.ui.card import card
from bastion_ui.routes._shared import link_card, public_page


def check_page() -> rx.Component:
    return public_page(
        "Check a public Bitcoin address",
        card(
            rx.text(
                "Bitcoin Bastion Trace provides advisory intelligence based on available sources."
            ),
            rx.text(
                "It is not legal verification, not Bitcoin consensus proof, and not "
                "a guarantee of safety."
            ),
            rx.text("Never enter seed phrases, private keys, wallet files, or signing material."),
            title="Trace Lite",
            variant="safety",
        ),
        trace_public_flow(),
        link_card("Open Bastion Trace", "/trace", "Use the broader Trace landing page."),
        subtitle="Focused public-address check flow.",
    )
