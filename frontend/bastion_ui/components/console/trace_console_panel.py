from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.console.degraded_state_banner import degraded_state_banner
from bastion_ui.components.console.module_status_card import module_status_card
from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card
from bastion_ui.topology import path_for

TRACE_CONSOLE_SAFETY_COPY = (
    "Advisory-only. Not legal verification. Not Bitcoin consensus proof. No custody. "
    "Public Bitcoin addresses only. Never enter seed phrases, private keys, "
    "wallet files or signing material."
)


def trace_console_panel() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            rx.heading("Trace Console", size="6"),
            rx.text("Monitor Trace activity, open reports, and review degraded provider context."),
            card(rx.text(TRACE_CONSOLE_SAFETY_COPY), title="Trace safety banner", variant="safety"),
            module_status_card(
                "Trace module status",
                "baseline",
                description=(
                    "Recent Trace report listing is a baseline placeholder "
                    "until a backend listing endpoint exists."
                ),
            ),
            degraded_state_banner(),
            card(
                rx.text("Recent Trace reports panel"),
                rx.text(
                    "No production report list is fabricated. "
                    "Future endpoint: GET /api/v1/trace/recent."
                ),
                title="Recent reports",
                badge=badge("placeholder", "warning"),
                variant="console",
            ),
            card(
                rx.text("Report lookup by report_id is read-only and accepts report ids only."),
                rx.link("Open public Trace entry", href=path_for("trace")),
                rx.link("Address check shortcut", href=path_for("check")),
                rx.link(
                    "Trace reports use /trace/{report_id} when a report id is available",
                    href=path_for("trace"),
                ),
                rx.link(
                    "Proof Packets use /trace/{report_id}/proof-packet when available",
                    href=path_for("trace"),
                ),
                title="Report lookup and shortcuts",
                variant="console",
            ),
            card(
                rx.text("Trace depends on available public Bitcoin and provider data."),
                rx.text("Providers may disagree, return stale data, or omit optional fields."),
                rx.text("Operators must manually review high-impact decisions."),
                title="Trace limitations",
                variant="console",
            ),
            align="start",
            spacing="4",
            width="100%",
        ),
    )
