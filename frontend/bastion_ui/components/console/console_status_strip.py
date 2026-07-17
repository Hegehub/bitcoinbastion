from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

STATUS_ITEMS: tuple[tuple[str, str], ...] = (
    ("API", "unknown"),
    ("Trace", "unknown"),
    ("Evidence", "unknown"),
    ("Providers", "unknown"),
    ("Market", "unknown"),
    ("Policy", "unknown"),
    ("Audit", "unknown"),
    ("Runtime", "unknown"),
)


def console_status_strip() -> rx.Component:
    return card(
        rx.hstack(
            *[
                rx.vstack(rx.text(label, weight="bold"), badge(status, "warning"))
                for label, status in STATUS_ITEMS
            ],
            wrap="wrap",
            spacing="4",
        ),
        title="Console status",
        subtitle="Unknown is the safe default until backend status is available.",
        variant="console",
    )
