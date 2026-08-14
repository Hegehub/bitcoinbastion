from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.state.shell_state import ShellState
from bastion_ui.theme.tokens import COLOR


def _crumb(item: rx.Var[dict[str, str]]) -> rx.Component:
    return cast(
        rx.Component,
        rx.el.li(
            rx.cond(
                item["current"] == "true",  # type: ignore[index]
                rx.text(item["title"], aria_current="page"),  # type: ignore[index]
                rx.link(item["title"], href=item["path"]),  # type: ignore[index]
            )
        ),
    )


def shell_route_context() -> rx.Component:
    return cast(
        rx.Component,
        rx.box(
            rx.text(ShellState.route_context, size="1", color=COLOR["text_secondary"]),
            rx.el.nav(
                rx.el.ol(rx.foreach(ShellState.breadcrumb_items, _crumb)),
                aria_label="Breadcrumb",
            ),
            aria_label="Current application context",
            padding="12px 24px 0",
        ),
    )
