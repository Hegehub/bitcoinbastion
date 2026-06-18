from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.card import card


def trace_evidence_summary(report_id: str = "") -> rx.Component:
    href = f"/trace/{report_id}/proof-packet" if report_id else "/trace/[report_id]/proof-packet"
    return card(
        rx.text("Evidence packet: Not available until provided by backend."),
        rx.text("Freshness: Not available."),
        rx.text("Manual review recommended when evidence is missing or limited."),
        rx.link("Open proof packet", href=href),
        title="Evidence summary",
    )
