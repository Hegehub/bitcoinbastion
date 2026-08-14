from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.trace.trace_safety_banner import trace_safety_banner
from bastion_ui.components.ui.card import card
from bastion_ui.state.trace_report_state import TraceReportState
from bastion_ui.topology import dynamic_route_parts


def proof_packet_viewer() -> rx.Component:
    report_prefix, report_suffix = dynamic_route_parts("trace.report", "report_id")
    return cast(
        rx.Component,
        rx.vstack(
            trace_safety_banner(),
            card(
                rx.text("Report id: ", TraceReportState.trace_report_id),
                rx.text(TraceReportState.proof_packet_status_label),
                rx.text(
                    "Evidence metadata, source lists, fingerprints, and timestamps are shown "
                    "only if the backend provides them."
                ),
                rx.text("No example fingerprints are displayed as real proof data."),
                rx.link(
                    "Back to Trace report",
                    href=report_prefix + TraceReportState.trace_report_id + report_suffix,
                ),
                title="Proof packet",
                variant="evidence",
            ),
            card(
                rx.text(
                    "Proof packets are advisory, source-dependent, and may require backend access "
                    "not exposed to the public Reflex shell yet."
                ),
                title="Proof packet limitations",
                variant="safety",
            ),
            align="start",
            spacing="4",
            width="100%",
        ),
    )
