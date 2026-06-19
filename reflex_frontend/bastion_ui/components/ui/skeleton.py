from __future__ import annotations

from typing import Literal, cast

import reflex as rx

from bastion_ui.theme.tokens import BASTION_PANEL_SOFT

SkeletonVariant = Literal["card", "line", "table", "metric"]


def skeleton(variant: SkeletonVariant = "line") -> rx.Component:
    sizes = {
        "card": ("100%", "140px"),
        "line": ("100%", "18px"),
        "table": ("100%", "220px"),
        "metric": ("180px", "80px"),
    }
    width, height = sizes[variant]
    return cast(
        rx.Component,
        rx.box(width=width, height=height, border_radius="12px", background=BASTION_PANEL_SOFT),
    )
