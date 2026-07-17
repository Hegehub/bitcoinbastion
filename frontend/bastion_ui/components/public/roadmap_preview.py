from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.public.pillar_card import pillar_card

CONSERVATIVE_STATUS_LABELS = (
    "implemented",
    "baseline",
    "experimental",
    "planned",
    "blocked",
    "future",
)


def roadmap_preview() -> rx.Component:
    items = (
        (
            "FastAPI backend",
            "Backend remains the source of truth for domain behavior.",
            "implemented",
        ),
        ("Reflex frontend", "Parallel frontend foundation and public routes.", "baseline"),
        ("Trace route parity", "Trace Lite and report workflows are later prompts.", "planned"),
        ("Market parity", "Jinja dashboard remains available until Reflex parity.", "future"),
    )
    return responsive_grid(*[pillar_card(title, body, label) for title, body, label in items])
