from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.theme.tokens import BASTION_BORDER, BASTION_GRAY


def public_footer() -> rx.Component:
    links = ("Trace", "Evidence", "Status", "Developers", "Operations", "Docs", "Security", "Roadmap", "Console")
    return cast(rx.Component, rx.box(
        rx.vstack(
            rx.heading("Bitcoin Bastion", size="4"),
            rx.text("No custody · Evidence over claims", color=BASTION_GRAY),
            rx.text("Bitcoin Bastion is not a wallet, not a custodian, not legal verification, and not Bitcoin consensus proof."),
            rx.flex(*[rx.link(link, href=f"/{link.lower()}") for link in links], wrap="wrap", gap="1rem"),
            max_width="1180px",
            padding="2rem 1rem",
            width="100%",
        ),
        border_top=f"1px solid {BASTION_BORDER}",
        width="100%",
    ))
