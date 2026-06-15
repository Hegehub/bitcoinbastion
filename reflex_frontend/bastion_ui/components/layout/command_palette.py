from __future__ import annotations

from typing import Final, cast

import reflex as rx

COMMAND_ACTIONS: Final[tuple[tuple[str, str], ...]] = (
    ("Open Platform", "/platform"),
    ("Open Trace", "/trace"),
    ("Check Bitcoin Address", "/check"),
    ("Open Trace Report", "/trace/{report_id}"),
    ("Open Proof Packet", "/trace/{report_id}/proof-packet"),
    ("Open Evidence", "/evidence"),
    ("Open Status", "/status"),
    ("Open Developers", "/developers"),
    ("Open Operations", "/operations"),
    ("Open Docs", "/docs"),
    ("Open Security", "/security"),
    ("Open Roadmap", "/roadmap"),
    ("Open Console", "/console"),
    ("Open Command Center", "/console/command-center"),
    ("Open Trace Radar", "/console/trace"),
    ("Open Evidence Chain", "/console/evidence"),
    ("Open Provider Trust Matrix", "/console"),
    ("Open Time Machine Timeline", "/console/time-machine"),
    ("Open Sovereign Grid Map", "/console/sovereign-grid"),
    ("Open Policy Simulator", "/console/policy"),
    ("Open Audit Replay", "/console/audit"),
    ("Open API Contract Explorer", "/console/audit"),
    ("Open Console Trace", "/console/trace"),
    ("Open Console Evidence", "/console/evidence"),
    ("Open Provider Health", "/console/provider-health"),
    ("Open Market Intelligence", "/console/market-intelligence"),
    ("Open Time Machine", "/console/time-machine"),
    ("Open Sovereign Grid", "/console/sovereign-grid"),
    ("Open Policy Engine", "/console/policy"),
    ("Open Audit Log", "/console/audit"),
    ("Open Deployment Status", "/console/deployment"),
    ("Open API Explorer", "/console/api-explorer"),
)


def command_palette() -> rx.Component:
    return cast(rx.Component, rx.box(
        rx.text("Command palette", weight="bold"),
        rx.flex(*[rx.link(label, href=href) for label, href in COMMAND_ACTIONS], wrap="wrap", gap="0.5rem"),
        border="1px solid #E5E7EB",
        border_radius="14px",
        padding="0.75rem",
        background="white",
        width="100%",
    ))
