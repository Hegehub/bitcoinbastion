from __future__ import annotations

from typing import Literal, cast

import reflex as rx

from bastion_ui.theme.styles import PANEL

MetricState = Literal["neutral", "success", "warning", "danger"]


def metric_card(
    label: str,
    value: str,
    *,
    description: str | None = None,
    trend: str | None = None,
    state: MetricState = "neutral",
) -> rx.Component:
    return cast(
        rx.Component,
        rx.box(
            rx.vstack(
                rx.text(label, color="#A3A3A3"),
                rx.heading(value, size="6"),
                rx.cond(description is not None, rx.text(description or "")),
                rx.cond(trend is not None, rx.text(trend or "")),
                rx.text(f"State: {state}"),
                align="start",
            ),
            style=PANEL,
        ),
    )
