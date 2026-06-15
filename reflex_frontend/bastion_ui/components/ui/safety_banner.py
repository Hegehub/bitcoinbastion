from __future__ import annotations

from typing import Literal, cast

import reflex as rx

from bastion_ui.security.safety_copy import TRACE_SAFETY_COPY
from bastion_ui.theme.styles import SAFETY_CARD
from bastion_ui.theme.tokens import BASTION_WARNING

SafetyVariant = Literal["trace", "proof_packet", "console"]


def safety_banner(variant: SafetyVariant = "trace") -> rx.Component:
    label = {"trace": "Trace safety", "proof_packet": "Proof Packet safety", "console": "Console safety"}[variant]
    return cast(rx.Component, rx.box(rx.text(label, weight="bold"), rx.text(TRACE_SAFETY_COPY), role="note", aria_label=label, style=SAFETY_CARD, width="100%"))


def no_custody_banner() -> rx.Component:
    return cast(rx.Component, rx.box(rx.text("No custody.", weight="bold"), rx.text("Never enter seed phrases, private keys, wallet files or signing material."), role="note", aria_label="No custody safety", style=SAFETY_CARD, width="100%"))


def advisory_banner() -> rx.Component:
    return cast(rx.Component, rx.box(rx.text("Advisory-only.", weight="bold"), rx.text("Not legal verification."), rx.text("Not Bitcoin consensus proof."), role="note", aria_label="Advisory safety", style=SAFETY_CARD, width="100%"))


def degraded_state_banner(message: str = "Some data may be delayed, degraded, or unavailable.") -> rx.Component:
    return cast(rx.Component, rx.box(rx.text(message, color=BASTION_WARNING), role="status", aria_label="Degraded state", style=SAFETY_CARD, width="100%"))
