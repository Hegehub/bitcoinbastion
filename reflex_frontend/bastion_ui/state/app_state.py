from __future__ import annotations

import reflex as rx


class AppState(rx.State):
    """Minimal shell state for the experimental Reflex app."""

    api_status: str = "not_checked"
