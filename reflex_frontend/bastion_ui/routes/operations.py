from __future__ import annotations

import reflex as rx

from bastion_ui.routes._shared import page_shell


def operations_page() -> rx.Component:
    return page_shell("Operations", "Self-hosted operation with evidence-driven deployment discipline.", (
        ("Self-hosted operation", "Bitcoin Bastion remains deployable without cloud lock-in."),
        ("Runtime direction", "Docker Compose, Kubernetes, K3s, and constrained profiles are documented with limitations."),
        ("Evidence-driven releases", "Deployment, migration, schema parity, provider health, and rollback evidence remain required."),
        ("Deployment limitations", "Runtime profiles are foundations and do not prove production readiness by themselves."),
        ("Observability", "Operators need metrics, logs, health checks, and incident evidence."),
        ("Degraded-mode visibility", "Delayed, degraded, fallback, or unavailable states must stay visible."),
    ))
