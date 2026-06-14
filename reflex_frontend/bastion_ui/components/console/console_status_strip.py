from __future__ import annotations

from typing import Literal, cast

import reflex as rx

from bastion_ui.components.ui.badge import badge

Status = Literal["available", "degraded", "fallback", "stale", "unavailable", "unknown"]
STATUS_CHIPS: tuple[tuple[str, Status], ...] = (
    ("API", "unknown"),
    ("Trace", "degraded"),
    ("Evidence", "fallback"),
    ("Market", "stale"),
    ("Providers", "unknown"),
    ("Policy", "degraded"),
    ("Runtime", "unknown"),
)


def console_status_strip() -> rx.Component:
    return cast(rx.Component, rx.hstack(*[badge(f"{name}: {status}", "warning" if status != "available" else "success") for name, status in STATUS_CHIPS], wrap="wrap"))
