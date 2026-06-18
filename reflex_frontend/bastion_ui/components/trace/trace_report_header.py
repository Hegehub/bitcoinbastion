from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.card import card


def trace_report_header(
    report_id: str = "Route report id", status: str = "Report loading"
) -> rx.Component:
    return card(
        rx.hstack(
            badge("Advisory-only", "info"),
            badge("No custody", "success"),
            badge(status, "warning"),
            wrap="wrap",
        ),
        rx.text(f"Report: {report_id}"),
        rx.text("Generated timestamp and confidence appear when the backend provides them."),
        title="Trace report",
        subtitle="Detailed public report view with visible limitations and degraded states.",
    )
