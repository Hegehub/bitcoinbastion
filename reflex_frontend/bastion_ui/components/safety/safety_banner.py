from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.safety.advisory_notice import advisory_notice
from bastion_ui.components.safety.no_custody_notice import no_custody_notice
from bastion_ui.theme.styles import SAFETY_CARD

REQUIRED_SAFETY_COPY = (
    "Advisory-only.",
    "Not legal verification.",
    "Not Bitcoin consensus proof.",
    "No custody.",
    "Public Bitcoin addresses only.",
    "Never enter seed phrases, private keys, wallet files or signing material.",
)


def trace_safety_banner() -> rx.Component:
    return cast(
        rx.Component,
        rx.box(
            rx.vstack(advisory_notice(), no_custody_notice(), align="start", spacing="2"),
            style=SAFETY_CARD,
        ),
    )
