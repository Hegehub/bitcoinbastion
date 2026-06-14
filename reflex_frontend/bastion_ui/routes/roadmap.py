from __future__ import annotations

import reflex as rx

from bastion_ui.routes._shared import page_shell


def roadmap_page() -> rx.Component:
    return page_shell("Roadmap", "Planned work remains evidence-driven and no-custody.", (
        ("Developer/API layer", "Expand API-oriented developer experiences safely."),
        ("Runtime profiles", "Validate profiles with real environment evidence."),
        ("Reflex frontend", "Build public pages first, then Trace and Console."),
        ("Trace improvements", "Prompt 26 will add Trace routes and public workflows."),
        ("Console", "Console routes are future work and not implemented here."),
        ("SDK/CLI/MCP", "Developer tooling continues around backend APIs."),
        ("Plugin API", "Plugins remain sandbox-limited and no-custody."),
    ))
