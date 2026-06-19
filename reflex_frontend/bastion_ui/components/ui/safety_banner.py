from __future__ import annotations

from typing import Literal

import reflex as rx

from bastion_ui.components.ui.alert import AlertVariant, alert

SafetyBannerVariant = Literal[
    "no_custody", "advisory", "degraded", "sensitive_input", "provider_disagreement"
]

SAFETY_BANNER_COPY: dict[SafetyBannerVariant, str] = {
    "no_custody": (
        "No custody. Public Bitcoin addresses only. Never enter seed phrases, private keys, "
        "wallet files or signing material."
    ),
    "advisory": (
        "Advisory-only. Not legal verification. Not Bitcoin consensus proof. No custody. "
        "Public Bitcoin addresses only. Never enter seed phrases, private keys, wallet files or "
        "signing material."
    ),
    "degraded": (
        "Evidence can be incomplete, stale, degraded, or provider-disputed. "
        "Manual review recommended."
    ),
    "sensitive_input": ("Sensitive wallet material is not accepted. Use public Bitcoin data only."),
    "provider_disagreement": (
        "Provider disagreement detected. Evidence sources do not fully agree. "
        "Manual review is recommended."
    ),
}


def safety_banner(variant: SafetyBannerVariant = "advisory") -> rx.Component:
    alert_variant: AlertVariant = (
        "degraded" if variant in {"degraded", "provider_disagreement"} else "advisory"
    )
    return alert(SAFETY_BANNER_COPY[variant], alert_variant)
