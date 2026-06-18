from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.alert import alert


def trace_status_banner(
    message: str = "Partial report: some panels may be unavailable or stale.",
) -> rx.Component:
    return alert(message, "degraded")
