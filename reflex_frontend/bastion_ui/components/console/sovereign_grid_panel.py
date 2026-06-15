from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.console._panel_helpers import preview_card

MODULES: tuple[tuple[str, str], ...] = (
    ("FastAPI Backend", "Backend source of truth; dependency status placeholder."),
    ("PostgreSQL", "Persistence layer; limitations and backup state placeholder."),
    ("Redis", "Broker/cache; fallback state placeholder."),
    ("Celery Worker", "Background jobs; degraded state placeholder."),
    ("Celery Beat", "Schedules; stale state placeholder."),
    ("Provider Health", "Provider visibility; unavailable state placeholder."),
    ("Evidence Layer", "Evidence/replay; dependency status placeholder."),
    ("Trace", "Trace context; advisory-only limitations."),
    ("Market Intelligence", "Informational market context only."),
    ("Policy Engine", "Operator review; no execution."),
    ("Webhooks/Event Bus", "Delivery status placeholder."),
    ("Runtime Profiles", "Deployment profile evidence placeholder."),
)


def sovereign_grid_panel() -> rx.Component:
    return cast(rx.Component, rx.grid(*[preview_card(name, purpose) for name, purpose in MODULES], columns="3", spacing="4", width="100%"))
