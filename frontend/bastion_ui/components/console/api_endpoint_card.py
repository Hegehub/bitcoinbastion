from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

SAFE_READ_ENDPOINTS = {
    "GET /api/v1/public/status",
    "GET /api/v1/public/roadmap",
    "GET /api/v1/public/features",
    "GET /api/v1/signals/top",
    "GET /api/v1/public/trace/{report_id}/summary",
}


def api_endpoint_card(method_path: str, category: str, safety: str) -> rx.Component:
    tryable = method_path in SAFE_READ_ENDPOINTS and safety == "Safe read"
    return card(
        rx.text("Category: " + category),
        rx.text("Safety classification: " + safety),
        rx.text("Try read-only request: " + ("available" if tryable else "not available")),
        title=method_path,
        badge=badge("tryable" if tryable else "inspection only", "info" if tryable else "warning"),
        variant="console",
    )
