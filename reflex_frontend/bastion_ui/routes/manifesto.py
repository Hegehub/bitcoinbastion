from __future__ import annotations

import reflex as rx

from bastion_ui.routes._shared import page_shell


def manifesto_page() -> rx.Component:
    return page_shell("Manifesto", "Principles for a sovereign Bitcoin-first backend.", (
        ("Bitcoin-first", "Bitcoin is the primary design reference."),
        ("Sovereignty-first", "Operators should be able to self-host and inspect their systems."),
        ("No custody", "Bitcoin Bastion is not a wallet and does not hold signing material."),
        ("Evidence over claims", "Readiness and intelligence claims require artifacts."),
        ("Operator control", "Risky actions require explicit operator awareness."),
        ("Local/self-hosted capable", "The system should work on private infrastructure."),
        ("No black-box trust", "Providers are fallible and observable."),
        ("Explicit limitations", "Advisory, degraded, fallback, and baseline states stay visible."),
    ))
