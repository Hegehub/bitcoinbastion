from __future__ import annotations

import reflex as rx

from bastion_ui.components.public.feature_grid import feature_grid
from bastion_ui.routes._shared import public_page


def platform_page() -> rx.Component:
    features = (
        (
            "FastAPI backend",
            "The backend remains the source of data and domain behavior.",
            "implemented",
        ),
        ("Trace layer", "Trace endpoints power later address and report workflows.", "baseline"),
        (
            "Evidence layer",
            "Evidence explains source material, limits, and review context.",
            "baseline",
        ),
        (
            "Market Intelligence",
            "Market Time Machine remains delegated until parity is proven.",
            "planned",
        ),
        (
            "Policy / operator control",
            "Review-first workflows must not auto-execute risky actions.",
            "baseline",
        ),
        (
            "Runtime / deployment",
            "Self-hosted profiles are tracked with conservative readiness labels.",
            "baseline",
        ),
        (
            "Developer API",
            "Public and service APIs are exposed through the backend contract.",
            "baseline",
        ),
        (
            "No custody",
            "The platform does not request wallet secrets or signing material.",
            "implemented",
        ),
    )
    return public_page(
        "Platform",
        feature_grid(features),
        subtitle="Bitcoin-first sovereign intelligence and operations infrastructure.",
    )
