from __future__ import annotations

from typing import Literal

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

SAFE_STATUS_LABELS = {"healthy", "degraded", "stale", "unavailable", "unknown", "baseline"}


def module_status_card(
    title: str,
    status: str = "unknown",
    *,
    description: str,
    last_updated: str = "Not available",
) -> rx.Component:
    safe_status = status if status in SAFE_STATUS_LABELS else "unknown"
    variant: Literal["success", "warning"] = "success" if safe_status == "healthy" else "warning"
    return card(
        rx.text(description),
        rx.text("Last updated: " + last_updated),
        title=title,
        subtitle="Unknown is not treated as healthy.",
        badge=badge(safe_status, variant),
        variant="console",
    )
