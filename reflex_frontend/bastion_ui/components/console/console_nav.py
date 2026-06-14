from __future__ import annotations

from typing import Final, cast

import reflex as rx

CONSOLE_NAV_ITEMS: Final[tuple[tuple[str, str], ...]] = (
    ("Dashboard", "/console"),
    ("Trace", "/console/trace"),
    ("Evidence", "/console/evidence"),
    ("Provider Health", "/console/provider-health"),
    ("Market Intelligence", "/console/market-intelligence"),
    ("Time Machine", "/console/time-machine"),
    ("Sovereign Grid", "/console/sovereign-grid"),
    ("Policy Engine", "/console/policy"),
    ("Audit Log", "/console/audit"),
    ("Deployment Status", "/console/deployment"),
    ("API Explorer", "/console/api-explorer"),
)


def console_nav() -> rx.Component:
    return cast(rx.Component, rx.vstack(*[rx.link(label, href=href) for label, href in CONSOLE_NAV_ITEMS], align="start", min_width="220px"))
