from __future__ import annotations

import reflex as rx

from bastion_ui.components.data.status_table import status_table
from bastion_ui.components.ui.card import card

CONSERVATIVE_ROADMAP_STATUSES = (
    "implemented",
    "baseline",
    "experimental",
    "planned",
    "blocked",
    "future",
)

ROADMAP_ROWS = [
    {
        "Area": "FastAPI backend",
        "Status": "implemented",
        "Notes": "Source of truth remains backend.",
    },
    {"Area": "Reflex scaffold", "Status": "baseline", "Notes": "Parallel shell and design system."},
    {
        "Area": "Trace public flow",
        "Status": "planned",
        "Notes": "Prompt 7 handles /check and /trace.",
    },
    {
        "Area": "Market dashboard",
        "Status": "future",
        "Notes": "FastAPI/Jinja remains during parity.",
    },
    {"Area": "Cutover", "Status": "blocked", "Notes": "Requires route/API/safety parity."},
]


def roadmap_preview() -> rx.Component:
    return card(status_table(ROADMAP_ROWS), title="Roadmap preview")
