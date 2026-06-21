from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.navigation import PUBLIC_NAV_ITEMS, TRACE_SAFETY_NOTE
from bastion_ui.state.navigation_state import NavigationState


def mobile_nav_trigger() -> rx.Component:
    return cast(
        rx.Component,
        rx.button(
            "Menu",
            on_click=NavigationState.toggle_mobile_nav,
            aria_label="Open mobile navigation",
        ),
    )


def mobile_nav() -> rx.Component:
    items = (*PUBLIC_NAV_ITEMS,)
    return cast(
        rx.Component,
        rx.vstack(
            rx.text("Mobile navigation"),
            *[rx.link(item.label, href=item.route) for item in items],
            rx.link("Check Bitcoin Address", href="/check"),
            rx.link("Console", href="/console"),
            rx.text(TRACE_SAFETY_NOTE),
            align="start",
            spacing="3",
            display=rx.cond(NavigationState.mobile_nav_open, "flex", "none"),
        ),
    )
