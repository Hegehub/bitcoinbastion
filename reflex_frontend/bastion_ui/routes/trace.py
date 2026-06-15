from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.layout.public_layout import public_layout
from bastion_ui.components.trace.address_check_form import address_check_form
from bastion_ui.components.trace.trace_limitations_card import trace_limitations_card
from bastion_ui.components.ui.safety_banner import safety_banner


def trace_page() -> rx.Component:
    return public_layout(cast(rx.Component, rx.vstack(
        rx.heading("Bastion Trace", size="7"),
        rx.text("Trace provides advisory, evidence-oriented context for public Bitcoin addresses."),
        safety_banner("trace"),
        address_check_form(),
        trace_limitations_card(),
        rx.text("Trace limitations are visible; degraded, fallback, stale, unavailable, and advisory states are not hidden."),
        spacing="5",
        align="start",
        width="100%",
    )))
