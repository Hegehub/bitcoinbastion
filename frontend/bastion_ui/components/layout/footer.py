from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.navigation import CANONICAL_NAVIGATION
from bastion_ui.theme.tokens import BASTION_BORDER, COLOR
from bastion_ui.topology import RouteClass, path_for

FOOTER_SAFETY_COPY = (
    "Bitcoin Bastion is advisory-only software. It does not custody funds, request seed "
    "phrases, or provide legal verification."
)


def footer() -> rx.Component:
    return cast(
        rx.Component,
        rx.box(
            rx.vstack(
                rx.hstack(
                    *[
                        rx.link(item.title, href=path_for(item.id))
                        for item in CANONICAL_NAVIGATION
                        if item.route_class in {RouteClass.PUBLIC, RouteClass.ACCESS_AWARE}
                    ],
                    spacing="4",
                    wrap="wrap",
                ),
                rx.text(FOOTER_SAFETY_COPY, color=COLOR["text_secondary"]),
                align="start",
                spacing="3",
            ),
            border_top=f"1px solid {BASTION_BORDER}",
            padding="24px",
        ),
    )
