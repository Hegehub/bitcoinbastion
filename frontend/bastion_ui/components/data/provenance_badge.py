from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.theme.tokens import COLOR


def provenance_badge(
    state: str | rx.Var[str],
    *,
    source: str | rx.Var[str],
    details: str | rx.Var[str] = "",
) -> rx.Component:
    """Accessible text-first provenance marker; color is supplemental only."""
    label = rx.text.span("Source: ", rx.text.strong(state))
    return cast(
        rx.Component,
        rx.tooltip(
            rx.badge(
                rx.hstack(rx.text("●", aria_hidden="true"), label, spacing="1"),
                variant="outline",
                color_scheme="gray",
                tab_index=0,
                aria_label=state,
                data_provenance=state,
                style={
                    "border": "2px solid currentColor",
                    "color": COLOR["text_secondary"],
                    "background": COLOR["matte"],
                    "transition": "none",
                    "outline_offset": "3px",
                },
            ),
            content=details,
        ),
    )
