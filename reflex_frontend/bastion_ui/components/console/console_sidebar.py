from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.navigation import CONSOLE_NAV_ITEMS

PRIMARY_CONSOLE_ROUTES = {
    "/console",
    "/console/trace",
    "/console/evidence",
    "/console/provider-health",
    "/console/market-intelligence",
    "/console/time-machine",
    "/console/sovereign-grid",
    "/console/policy",
    "/console/audit",
    "/console/api-explorer",
}


def console_sidebar() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            rx.heading("Bastion Console", size="4"),
            *[
                rx.link(
                    rx.hstack(
                        rx.text(item.label),
                        badge(
                            "ready" if item.route in PRIMARY_CONSOLE_ROUTES else "coming next",
                            "info" if item.route in PRIMARY_CONSOLE_ROUTES else "warning",
                        ),
                        spacing="2",
                    ),
                    href=item.route,
                )
                for item in CONSOLE_NAV_ITEMS
            ],
            align="start",
            spacing="3",
            min_width="260px",
        ),
    )
