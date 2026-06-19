from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.public.pillar_card import pillar_card


def feature_grid(features: tuple[tuple[str, str, str], ...]) -> rx.Component:
    return responsive_grid(
        *[pillar_card(title, body, status=status) for title, body, status in features]
    )
