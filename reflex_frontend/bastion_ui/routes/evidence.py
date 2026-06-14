from __future__ import annotations

import reflex as rx

from bastion_ui.routes._shared import page_shell


def evidence_page() -> rx.Component:
    return page_shell("Evidence", "Evidence packets and replay make backend claims auditable.", (
        ("Evidence packets", "Packets capture source context, lineage, limitations, and review state."),
        ("Replay", "Replay helps operators inspect how a result was produced."),
        ("Provider evidence", "Provider health and source quality are part of the operator view."),
        ("Deployment evidence", "Release and deployment artifacts are required for readiness claims."),
        ("Limitations", "Evidence can be incomplete, stale, degraded, or unavailable."),
        ("Correlation is not causation", "Market context remains informational and does not prove causation."),
    ))
