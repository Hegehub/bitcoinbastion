from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.console.degraded_state_banner import degraded_state_banner
from bastion_ui.components.console.module_status_card import module_status_card
from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

AUDIT_BASELINE_COPY = (
    "Audit Console baseline view. Immutable audit storage is not claimed by this Reflex module."
)


def audit_log_panel() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            rx.heading("Audit Console", size="6"),
            rx.text(
                "Review frontend-facing audit and operational log summaries "
                "when backend data is available."
            ),
            card(rx.text(AUDIT_BASELINE_COPY), title="Audit baseline", variant="safety"),
            module_status_card(
                "Audit module status",
                "baseline",
                description=(
                    "No global audit event endpoint is connected yet; "
                    "future endpoint: GET /api/v1/audit/events."
                ),
            ),
            degraded_state_banner(),
            card(
                rx.text(
                    "Recent audit events are not fabricated. Empty state remains explicit "
                    "until a backend endpoint exists."
                ),
                rx.text(
                    "Potential references: evidence events, observability events, "
                    "webhook delivery logs, and Trace report events."
                ),
                title="Recent audit events",
                badge=badge("placeholder", "warning"),
                variant="console",
            ),
            card(
                rx.text(
                    "Frontend migration audit status is documented in migration progress files."
                ),
                rx.link("Open migration baseline", href="/docs"),
                title="Migration audit references",
                variant="console",
            ),
            card(
                rx.text("This is not a WORM audit backend implementation."),
                rx.text(
                    "Audit hardening, retention, immutable storage, and export controls "
                    "remain future backend work."
                ),
                title="Audit limitations",
                variant="console",
            ),
            align="start",
            spacing="4",
            width="100%",
        ),
    )
