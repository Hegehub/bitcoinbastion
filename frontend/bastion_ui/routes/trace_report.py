from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.evidence.degraded_evidence_banner import degraded_evidence_banner
from bastion_ui.components.layout.grid import responsive_grid
from bastion_ui.components.trace.trace_confidence_panel import trace_confidence_panel
from bastion_ui.components.trace.trace_evidence_summary import trace_evidence_summary
from bastion_ui.components.trace.trace_limitations_card import trace_limitations_card
from bastion_ui.components.trace.trace_overview_card import trace_overview_card
from bastion_ui.components.trace.trace_report_header import trace_report_header
from bastion_ui.components.trace.trace_safety_banner import trace_safety_banner
from bastion_ui.components.trace.trace_status_banner import trace_status_banner
from bastion_ui.components.trace.trace_topology import current_trace_topology
from bastion_ui.routes._shared import link_card, public_page
from bastion_ui.routes.system import not_found_page
from bastion_ui.state.trace_report_state import TraceReportState


def trace_report_page() -> rx.Component:
    content = public_page(
        "Trace report",
        trace_report_header(),
        trace_safety_banner(),
        trace_status_banner(),
        degraded_evidence_banner(),
        rx.cond(TraceReportState.error != "", rx.text(TraceReportState.error)),
        responsive_grid(
            trace_overview_card(),
            trace_confidence_panel(),
            trace_evidence_summary(),
        ),
        trace_limitations_card(),
        current_trace_topology(),
        responsive_grid(link_card("Back to Trace", "/trace", "Start another address review.")),
        subtitle="Detailed advisory Trace report. Dynamic data loads only from backend APIs.",
    )
    return cast(
        rx.Component,
        rx.cond(
            TraceReportState.route_validated & TraceReportState.route_valid,
            content,
            not_found_page(),
        ),
    )
