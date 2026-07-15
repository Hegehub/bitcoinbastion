from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.console.degraded_state_banner import degraded_state_banner
from bastion_ui.components.console.module_status_card import module_status_card
from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

PROVIDER_HEALTH_BASELINE_COPY = (
    "Global provider health endpoint is not connected yet. "
    "Unknown provider state is never displayed as healthy."
)


def provider_health_panel() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            rx.heading("Provider Health", size="6"),
            rx.text(
                "Review provider availability, stale data warnings, and "
                "provider disagreement notes."
            ),
            module_status_card(
                "Overall provider status",
                "unknown",
                description=PROVIDER_HEALTH_BASELINE_COPY,
            ),
            degraded_state_banner(),
            card(
                rx.text("Supported status types: healthy, degraded, stale, unavailable, unknown."),
                rx.text(
                    "Current baseline: unknown until backend provider health data is available."
                ),
                title="Provider health matrix",
                badge=badge("unknown", "warning"),
                variant="console",
            ),
            card(
                rx.text(
                    "Degraded provider list is empty because no global provider "
                    "endpoint is connected."
                ),
                rx.text("Future endpoint: GET /api/v1/provider-health."),
                title="Degraded and stale providers",
                variant="console",
            ),
            card(
                rx.text(
                    "Provider disagreement can reduce confidence and should trigger manual review."
                ),
                rx.text(
                    "Operational decisions should account for stale, fallback, "
                    "and unavailable data."
                ),
                title="Operational limitations",
                variant="console",
            ),
            align="start",
            spacing="4",
            width="100%",
        ),
    )
