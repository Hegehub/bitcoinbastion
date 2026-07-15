from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.console.degraded_state_banner import degraded_state_banner
from bastion_ui.components.console.module_status_card import module_status_card
from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card

EVIDENCE_CONSOLE_BASELINE_COPY = (
    "Evidence Console baseline view. Backend evidence listing endpoint is not available yet. "
    "Use report-specific evidence endpoints where available."
)


def evidence_console_panel() -> rx.Component:
    return cast(
        rx.Component,
        rx.vstack(
            rx.heading("Evidence Console", size="6"),
            rx.text(
                "Review evidence packets, Proof Packet references, and "
                "audit-oriented evidence summaries."
            ),
            card(
                rx.text(EVIDENCE_CONSOLE_BASELINE_COPY), title="Evidence baseline", variant="safety"
            ),
            module_status_card(
                "Evidence module status",
                "baseline",
                description=(
                    "Global evidence packet listing is not connected; "
                    "report-specific evidence endpoints remain available."
                ),
            ),
            degraded_state_banner(),
            card(
                rx.text(
                    "Evidence packet lookup uses report-specific endpoints and does not "
                    "fabricate packet rows."
                ),
                rx.text(
                    "Fields displayed when available: packet id, report id, source, "
                    "timestamp, confidence, freshness, and stale/degraded flags."
                ),
                title="Evidence packet lookup",
                badge=badge("read-only", "info"),
                variant="console",
            ),
            card(
                rx.link("Open Evidence overview", href="/evidence"),
                rx.link("Open Trace to choose a report", href="/trace"),
                rx.text(
                    "Proof Packet links are report-specific and remain unavailable "
                    "until a report id is present."
                ),
                title="Evidence and Proof Packet shortcuts",
                variant="console",
            ),
            card(
                rx.text(
                    "Evidence is advisory source material, not absolute proof "
                    "or legal verification."
                ),
                rx.text(
                    "Source freshness and degraded provider state must remain visible to operators."
                ),
                title="Evidence limitations",
                variant="console",
            ),
            align="start",
            spacing="4",
            width="100%",
        ),
    )
