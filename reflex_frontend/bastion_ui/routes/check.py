from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.layout.public_layout import public_layout
from bastion_ui.components.trace.address_check_form import address_check_form
from bastion_ui.components.ui.safety_banner import safety_banner


def check_page() -> rx.Component:
    return public_layout(cast(rx.Component, rx.vstack(
        rx.heading("Bitcoin Address Check", size="7"),
        rx.text("Only public Bitcoin addresses are accepted. FastAPI remains the source of truth."),
        safety_banner("trace"),
        address_check_form(),
        rx.link("Learn more in Bastion Trace", href="/trace"),
        spacing="5",
        align="start",
        width="100%",
    )))
