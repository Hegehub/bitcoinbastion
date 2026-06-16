from __future__ import annotations

from typing import Literal, cast

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.theme.typography import METRIC

MetricState = Literal["neutral", "success", "warning", "danger", "info"]


def metric_card(
    label: str,
    value: str,
    *,
    description: str = "Informational metric.",
    trend: str | None = None,
    state: MetricState = "neutral",
) -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            rx.hstack(
                rx.text(label, weight="bold"),
                badge(state.title(), state),
                justify="between",
            ),
            rx.text(value, style=METRIC),
            rx.text(description, color="gray"),
            rx.cond(trend is not None, rx.text(trend or "", color="gray")),
            align="start",
            spacing="2",
        ),
    )
