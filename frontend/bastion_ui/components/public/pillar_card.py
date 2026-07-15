from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import BadgeVariant, badge
from bastion_ui.components.ui.card import card


def pillar_card(
    title: str,
    description: str,
    label: str = "baseline",
    variant: BadgeVariant = "info",
) -> rx.Component:
    return card(
        rx.text(description),
        title=title,
        badge=badge(label, variant),
    )
