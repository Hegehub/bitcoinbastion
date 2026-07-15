from __future__ import annotations

from typing import cast

import reflex as rx

MARKET_SECTION_LINKS: tuple[tuple[str, str], ...] = (
    ("Time Machine", "/market/time-machine"),
    ("Timeline", "/market/timeline"),
    ("Signals", "/market/signals"),
    ("Evidence", "/market/evidence"),
    ("Narratives", "/market/narratives"),
    ("Sources", "/market/sources"),
)


def market_section_nav() -> rx.Component:
    return cast(
        rx.Component,
        rx.hstack(
            *[rx.link(label, href=route) for label, route in MARKET_SECTION_LINKS],
            wrap="wrap",
            spacing="4",
        ),
    )
