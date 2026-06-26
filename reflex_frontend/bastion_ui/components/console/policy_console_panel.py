from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.console.degraded_state_banner import degraded_state_banner
from bastion_ui.components.console.module_status_card import module_status_card
from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

POLICY_CONSOLE_SAFETY_COPY = (
    "Policy Console is read-only. It can show policy facts, warnings, and requires-review states, "
    "but it cannot perform approvals, sending, trading, signing, or treasury actions."
)


def policy_console_panel() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            rx.heading("Policy Console", size="6"),
            rx.text(
                "Review policy facts, warnings, blocked states, and rule evaluation summaries."
            ),
            card(
                rx.text(POLICY_CONSOLE_SAFETY_COPY), title="Policy safety banner", variant="safety"
            ),
            module_status_card(
                "Policy module status",
                "baseline",
                description=(
                    "Policy facts can be loaded per Trace report when backend "
                    "report policy endpoints are available."
                ),
            ),
            degraded_state_banner(),
            card(
                rx.text("Policy facts lookup is report-id based and read-only."),
                rx.text(
                    "Endpoint used when available: /api/v1/trace/report/{report_id}/policy-facts."
                ),
                title="Policy facts lookup",
                badge=badge("read-only", "info"),
                variant="console",
            ),
            card(
                rx.text(
                    "Policy warnings and blocked/requires-review states are shown "
                    "as operator context only."
                ),
                rx.text(
                    "No direct wallet action, transaction authorization, or treasury "
                    "execution is exposed."
                ),
                title="Warnings and review states",
                variant="console",
            ),
            card(
                rx.text("Policy facts may be incomplete, stale, or unavailable."),
                rx.text(
                    "Operators must review evidence and provider limitations "
                    "before taking separate actions."
                ),
                title="Policy limitations",
                variant="console",
            ),
            align="start",
            spacing="4",
            width="100%",
        ),
    )
