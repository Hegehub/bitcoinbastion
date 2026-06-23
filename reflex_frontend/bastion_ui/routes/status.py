from __future__ import annotations

import reflex as rx

from bastion_ui.components.public.status_summary import status_fallback_card
from bastion_ui.components.ui.card import card
from bastion_ui.routes._shared import public_page


def status_page() -> rx.Component:
    return public_page(
        "Status",
        status_fallback_card(),
        card(
            rx.text(
                "Provider health and degraded-mode signals should be displayed when "
                "backend data is available."
            ),
            rx.text(
                "Timestamp and stale-data notices must remain visible when freshness is uncertain."
            ),
            title="Provider health and degraded mode",
        ),
        subtitle=(
            "Public status route using safe fallback behavior when live API data is unavailable."
        ),
    )
