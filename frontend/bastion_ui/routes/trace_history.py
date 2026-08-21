from __future__ import annotations

import reflex as rx

from bastion_ui.components.trace.trace_topology import historical_trace_topology
from bastion_ui.routes._shared import public_page


def trace_history_page() -> rx.Component:
    return public_page(
        "Historical Trace topology",
        historical_trace_topology(),
        subtitle="Exact immutable Graph Snapshot and historically bound analytical status.",
    )
