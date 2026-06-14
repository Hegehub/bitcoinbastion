from __future__ import annotations

from typing import cast

import reflex as rx


def trace_report_header(report_id: str = "pending") -> rx.Component:
    return cast(rx.Component, rx.vstack(rx.heading("Trace Report", size="7"), rx.text(f"Report ID: {report_id}"), align="start"))
