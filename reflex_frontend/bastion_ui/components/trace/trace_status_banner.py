from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.safety_banner import degraded_state_banner


def trace_status_banner() -> rx.Component:
    return degraded_state_banner("Trace data may be partial, delayed, degraded, stale, or unavailable.")
