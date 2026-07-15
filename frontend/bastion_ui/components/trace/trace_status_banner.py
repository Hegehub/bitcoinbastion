from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.ui.alert import alert
from bastion_ui.state.trace_report_state import TraceReportState


def trace_status_banner() -> rx.Component:
    return cast(
        rx.Component,
        rx.cond(
            TraceReportState.has_degraded_data,
            alert("Partial report. Some panels may be unavailable, limited, or stale.", "degraded"),
            alert("Complete report status depends on backend-provided panel data.", "advisory"),
        ),
    )
