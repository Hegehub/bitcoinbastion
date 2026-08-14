"""Application-level disabled and not-found surfaces."""

from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.routes._shared import public_page
from bastion_ui.topology import RouteRecord, breadcrumbs, path_for


def route_breadcrumbs(route: RouteRecord) -> rx.Component:
    trail = breadcrumbs(route.id)
    return cast(
        rx.Component,
        rx.el.nav(
            rx.el.ol(
                *[
                    rx.el.li(
                        rx.text(item.title)
                        if item.id == route.id
                        else rx.link(item.title, href=path_for(item.id)),
                        aria_current="page" if item.id == route.id else None,
                    )
                    for item in trail
                ]
            ),
            aria_label="Breadcrumb",
        ),
    )


def feature_disabled_page(*, title: str) -> rx.Component:
    return public_page(
        "Feature not enabled",
        rx.heading("Feature not enabled", size="5"),
        rx.text(
            f"{title} exists, but its frontend rollout is currently disabled. "
            "This is not an Access denial or a backend availability error."
        ),
        rx.link("Return to Bitcoin Bastion", href=path_for("overview.home"), role="button"),
        subtitle="No demo fixture or LIVE data was substituted.",
    )


def not_found_page() -> rx.Component:
    return public_page(
        "Page not found",
        rx.heading("Page not found", size="6"),
        rx.text("The requested application route does not exist or contains an invalid value."),
        rx.link("Return to Bitcoin Bastion", href=path_for("overview.home"), role="button"),
        subtitle="No framework internals or private identifiers are shown.",
    )
