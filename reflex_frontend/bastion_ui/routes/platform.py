from __future__ import annotations

import reflex as rx

from bastion_ui.routes._shared import page_shell


def platform_page() -> rx.Component:
    return page_shell("Platform", "FastAPI remains the source of truth for Bitcoin Bastion.", (
        ("FastAPI backend foundation", "API routes, validation, persistence, and service boundaries stay in the backend."),
        ("Evidence layer", "Evidence packets, replay records, and release artifacts support evidence over claims."),
        ("Provider health", "Providers are treated as fallible and visible, including degraded or stale states."),
        ("Market intelligence", "Market intelligence remains advisory and correlation-aware, not a trading oracle."),
        ("Trace", "Trace surfaces are future Reflex work; Prompt 26 implementation pending."),
        ("Treasury and policy modules", "Policy modules remain no-custody and require operator control."),
        ("Self-hosted deployment", "Compose, Kubernetes, K3s, and other profiles remain evidence-driven deployment paths."),
    ))
