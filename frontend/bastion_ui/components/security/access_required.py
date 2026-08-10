from __future__ import annotations

from typing import cast

import reflex as rx


def access_required_shell(heading: str | rx.Var[str], detail: str | rx.Var[str]) -> rx.Component:
    return cast(
        rx.Component,
        rx.callout(
            rx.vstack(
                rx.heading(heading, size="5", id="security-denial-heading"),
                rx.text(detail, id="security-denial-detail"),
                rx.link("Review Proof-of-Access options", href="/access", id="security-recovery"),
                align="start",
            ),
            role="alert",
            color_scheme="orange",
            variant="surface",
            id="access-required-shell",
        ),
    )
