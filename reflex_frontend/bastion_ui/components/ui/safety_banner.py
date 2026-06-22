from __future__ import annotations

from typing import Literal

import reflex as rx

from bastion_ui.components.ui.alert import alert
from bastion_ui.security.safety_copy import TRACE_PUBLIC_SAFETY_COPY

SafetyBannerVariant = Literal[
    "no_custody", "advisory", "degraded", "sensitive_input", "provider_disagreement"
]

SAFETY_BANNER_COPY: dict[SafetyBannerVariant, str] = {
    "no_custody": TRACE_PUBLIC_SAFETY_COPY,
    "advisory": TRACE_PUBLIC_SAFETY_COPY,
    "degraded": (
        "Evidence may be incomplete, stale, degraded, or unavailable. Manual review recommended."
    ),
    "sensitive_input": "Never enter seed phrases, private keys, wallet files or signing material.",
    "provider_disagreement": (
        "Provider disagreement detected. Evidence sources do not fully agree. "
        "Manual review is recommended."
    ),
}


def safety_banner(variant: SafetyBannerVariant = "advisory") -> rx.Component:
    if variant in {"degraded", "provider_disagreement"}:
        return alert(SAFETY_BANNER_COPY[variant], "degraded")
    return alert(SAFETY_BANNER_COPY[variant], "advisory")
