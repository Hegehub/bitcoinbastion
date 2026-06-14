from __future__ import annotations

import reflex as rx

from bastion_ui.routes._shared import page_shell


def status_page() -> rx.Component:
    return page_shell("Status", "Conservative baseline status for public Reflex surfaces.", (
        ("Backend API", "BASELINE / PENDING PRODUCTION EVIDENCE"),
        ("Trace", "IN PROGRESS / PROMPT 26 IMPLEMENTATION PENDING"),
        ("Market Intelligence", "BASELINE / PENDING PRODUCTION EVIDENCE"),
        ("Evidence", "BASELINE / PENDING PRODUCTION EVIDENCE"),
        ("Deployment", "BASELINE / PENDING PRODUCTION EVIDENCE"),
        ("Runtime profiles", "BASELINE / ENVIRONMENT VALIDATION PENDING"),
        ("Reflex frontend", "IN PROGRESS / NOT PRODUCTION PRIMARY"),
    ))
