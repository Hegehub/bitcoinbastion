from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.layout.command_palette import command_palette_trigger
from bastion_ui.components.layout.mobile_nav import mobile_nav, mobile_nav_trigger
from bastion_ui.navigation import CANONICAL_NAVIGATION
from bastion_ui.state.navigation_state import NavigationState
from bastion_ui.theme.styles import FOCUS_RING, GLASS_NAV
from bastion_ui.theme.tokens import BASTION_BORDER, COLOR
from bastion_ui.topology import RouteClass, path_for


def header() -> rx.Component:
    return cast(
        rx.Component,
        rx.box(
            rx.hstack(
                rx.link(
                    "Bitcoin Bastion",
                    href=path_for("overview.home"),
                    color=COLOR["brand"],
                    weight="bold",
                    style=FOCUS_RING,
                ),
                rx.hstack(
                    *[
                        rx.link(
                            rx.text(item.title),
                            href=path_for(item.id),
                            aria_current=rx.cond(
                                NavigationState.current_path == path_for(item.id), "page", None
                            ),
                            style=FOCUS_RING,
                            class_name="bb-nav-link",
                        )
                        for item in CANONICAL_NAVIGATION
                        if item.route_class in {RouteClass.PUBLIC, RouteClass.ACCESS_AWARE}
                    ],
                    spacing="3",
                    wrap="wrap",
                    display=["none", "none", "flex"],
                ),
                rx.spacer(),
                rx.box(command_palette_trigger(), display=["none", "none", "block"]),
                rx.button(
                    rx.color_mode_cond("Dark theme", "Light theme"),
                    on_click=rx.toggle_color_mode,
                    aria_label="Toggle light and dark theme",
                    style=FOCUS_RING,
                ),
                mobile_nav_trigger(),
                width="100%",
                align="center",
            ),
            mobile_nav(),
            border_bottom=f"1px solid {BASTION_BORDER}",
            padding="16px 24px",
            style=GLASS_NAV,
            class_name="bb-glass",
            position="sticky",
            top="0",
            z_index="20",
        ),
    )
