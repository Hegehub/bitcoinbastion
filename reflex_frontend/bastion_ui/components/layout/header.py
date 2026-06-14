from __future__ import annotations

from typing import Final, cast

import reflex as rx

from bastion_ui.components.layout.command_palette import command_palette
from bastion_ui.theme.responsive import DESKTOP_NAV_DISPLAY, MOBILE_NAV_DISPLAY
from bastion_ui.theme.tokens import BASTION_BORDER, BASTION_GRAPHITE, BITCOIN_ORANGE

NAV_ITEMS: Final[tuple[tuple[str, str], ...]] = (
    ("Platform", "/platform"),
    ("Trace", "/trace"),
    ("Evidence", "/evidence"),
    ("Status", "/status"),
    ("Developers", "/developers"),
    ("Operations", "/operations"),
    ("Docs", "/docs"),
    ("Security", "/security"),
    ("Roadmap", "/roadmap"),
    ("Console", "/console"),
)


def _nav_links() -> rx.Component:
    return cast(rx.Component, rx.hstack(*[rx.link(label, href=href, color=BASTION_GRAPHITE) for label, href in NAV_ITEMS], spacing="4"))


def public_header() -> rx.Component:
    return cast(rx.Component, rx.box(
        rx.vstack(
            rx.hstack(
                rx.link(rx.heading("Bitcoin Bastion", size="4", color=BITCOIN_ORANGE), href="/"),
                rx.spacer(),
                rx.box(_nav_links(), display=DESKTOP_NAV_DISPLAY),
                rx.link("Console", href="/console", color=BASTION_GRAPHITE),
                rx.box(rx.text("Menu: Platform · Trace · Evidence · Status · Developers · Operations · Docs · Security · Roadmap"), display=MOBILE_NAV_DISPLAY),
                align="center",
                width="100%",
            ),
            command_palette(),
            width="100%",
            max_width="1180px",
            padding="1rem",
        ),
        position="sticky",
        top="0",
        z_index="10",
        background="rgba(255,248,237,0.96)",
        border_bottom=f"1px solid {BASTION_BORDER}",
        backdrop_filter="blur(12px)",
        width="100%",
    ))
