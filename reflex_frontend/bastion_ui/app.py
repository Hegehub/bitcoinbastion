from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.theme.styles import CARD, SAFETY_CARD
from bastion_ui.theme.tokens import BASTION_BG, BASTION_GRAY


def index() -> rx.Component:
    """Render the isolated Reflex shell home page."""

    return cast(
        rx.Component,
        rx.center(
            rx.vstack(
                rx.heading("Bitcoin Bastion Reflex Frontend", size="7"),
                rx.text("Parallel migration shell.", color=BASTION_GRAY),
                rx.box(
                    rx.text(
                        "No custody. Never enter seed phrases, private keys, wallet files, "
                        "or signing material.",
                        weight="bold",
                    ),
                    style=SAFETY_CARD,
                    width="100%",
                ),
                rx.box(
                    rx.text("Frontend parity is not complete yet."),
                    rx.text("Next.js remains the active legacy frontend until cutover gates pass."),
                    style=CARD,
                    width="100%",
                ),
                spacing="5",
                width="100%",
                max_width="760px",
            ),
            min_height="100vh",
            padding="32px",
            background=BASTION_BG,
            color="white",
        ),
    )


app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="orange",
        radius="large",
    )
)

app.add_page(index, route="/", title="Bitcoin Bastion Reflex Frontend")
