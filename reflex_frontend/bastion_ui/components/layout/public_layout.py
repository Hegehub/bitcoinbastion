from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.layout.footer import public_footer
from bastion_ui.components.layout.header import public_header
from bastion_ui.theme.responsive import PAGE_MAX_WIDTH, PAGE_PADDING
from bastion_ui.theme.tokens import BASTION_BG_SOFT


def public_layout(content: rx.Component) -> rx.Component:
    """Render the shared public page layout."""

    return cast(rx.Component, rx.box(
        public_header(),
        rx.box(
            rx.box(content, max_width=PAGE_MAX_WIDTH, width="100%", padding=PAGE_PADDING),
            id="main-content",
            as_="main",
            width="100%",
        ),
        public_footer(),
        min_height="100vh",
        background=BASTION_BG_SOFT,
        display="flex",
        flex_direction="column",
        align_items="center",
    ))
