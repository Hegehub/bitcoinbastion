from __future__ import annotations

from typing import Literal, cast

import reflex as rx

SkeletonKind = Literal["card", "line", "table", "metric"]


def skeleton(kind: SkeletonKind = "line") -> rx.Component:
    heights = {"line": "18px", "card": "120px", "table": "220px", "metric": "96px"}
    return cast(
        rx.Component,
        rx.box(
            background="rgba(255,255,255,0.08)",
            border_radius="12px",
            height=heights[kind],
            width="100%",
        ),
    )
