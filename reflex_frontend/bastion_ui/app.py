from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.feedback.degraded_state import degraded_state
from bastion_ui.components.feedback.loading_state import loading_state
from bastion_ui.components.feedback.stale_data_banner import stale_data_banner
from bastion_ui.components.layout.command_palette import command_palette
from bastion_ui.components.layout.console_sidebar import console_sidebar
from bastion_ui.components.layout.footer import footer
from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.layout.header import header
from bastion_ui.components.layout.mobile_nav import mobile_nav
from bastion_ui.components.layout.public_layout import public_layout
from bastion_ui.components.safety.advisory_notice import advisory_notice
from bastion_ui.components.safety.no_custody_notice import no_custody_notice
from bastion_ui.components.safety.safety_banner import trace_safety_banner
from bastion_ui.components.ui.alert import alert
from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.button import button
from bastion_ui.components.ui.card import card
from bastion_ui.components.ui.metric import metric_card
from bastion_ui.theme.styles import CARD, SAFETY_CARD
from bastion_ui.theme.tokens import BASTION_BG, BASTION_GRAY


def index() -> rx.Component:
    """Render the isolated Reflex shell home page."""

    return cast(
        rx.Component,
        rx.center(
            rx.vstack(
                rx.heading("Bitcoin Bastion Reflex Frontend", size="7"),
                rx.text("Parallel migration shell.", color=BASTION_GRAY),
                rx.box(
                    rx.text(
                        "No custody. Never enter seed phrases, private keys, wallet files, "
                        "or signing material.",
                        weight="bold",
                    ),
                    style=SAFETY_CARD,
                    width="100%",
                ),
                rx.box(
                    rx.text("Frontend parity is not complete yet."),
                    rx.text("Next.js remains the active legacy frontend until cutover gates pass."),
                    style=CARD,
                    width="100%",
                ),
                spacing="5",
                width="100%",
                max_width="760px",
            ),
            min_height="100vh",
            padding="32px",
            background=BASTION_BG,
            color="white",
        ),
    )


def design_system_preview() -> rx.Component:
    """Render a development-only design-system preview."""

    return public_layout(
        rx.vstack(
            rx.badge("Development preview only", color_scheme="orange"),
            rx.heading("Design System Foundation", size="7"),
            rx.text("Reusable UI primitives for later public, Trace, Market, and Console pages."),
            trace_safety_banner(),
            header(),
            footer(),
            mobile_nav(),
            console_sidebar(),
            command_palette(),
            responsive_grid(
                card(
                    button("Primary action"),
                    button("Secondary action", "secondary"),
                    button("Ghost action", "ghost"),
                    title="Buttons",
                ),
                card(
                    badge("Advisory", "info"),
                    badge("Manual review recommended", "warning"),
                    badge("Elevated risk band", "risk_medium"),
                    title="Badges",
                ),
                card(
                    alert("This view may be incomplete.", "advisory"),
                    degraded_state(),
                    stale_data_banner(),
                    title="Alerts and feedback",
                ),
                card(
                    metric_card("Provider state", "Degraded", state="warning"),
                    loading_state(),
                    title="Metrics and loading",
                ),
                card(advisory_notice(), no_custody_notice(), title="Safety notices"),
            ),
            align="start",
            spacing="5",
            width="100%",
        )
    )


app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="orange",
        radius="large",
    )
)

app.add_page(index, route="/", title="Bitcoin Bastion Reflex Frontend")
