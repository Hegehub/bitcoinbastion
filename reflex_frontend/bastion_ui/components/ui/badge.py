from __future__ import annotations

from typing import Literal, cast

import reflex as rx

BadgeVariant = Literal["success", "warning", "danger", "neutral", "bitcoin"]


def badge(label: str, variant: BadgeVariant = "neutral") -> rx.Component:
    colors = {
        "success": "green",
        "warning": "yellow",
        "danger": "red",
        "neutral": "gray",
        "bitcoin": "orange",
    }
    return cast(rx.Component, rx.badge(label, color_scheme=colors[variant], variant="soft"))
