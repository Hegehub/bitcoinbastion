from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.navigation import CANONICAL_NAVIGATION
from bastion_ui.state.navigation_state import NavigationState
from bastion_ui.topology import RouteClass, path_for


def console_sidebar() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            rx.heading("Console", size="4"),
            *[
                rx.link(
                    rx.text(item.title),
                    href=path_for(item.id),
                    aria_current=rx.cond(
                        NavigationState.current_path == path_for(item.id), "page", None
                    ),
                )
                for item in CANONICAL_NAVIGATION
                if item.route_class is RouteClass.OPERATOR_ONLY
            ],
            align="start",
            spacing="3",
            min_width="260px",
        ),
    )
