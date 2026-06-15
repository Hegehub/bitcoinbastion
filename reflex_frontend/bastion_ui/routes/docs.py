from __future__ import annotations

import reflex as rx

from bastion_ui.routes._shared import page_shell


def docs_page() -> rx.Component:
    return page_shell("Docs", "Documentation entry points for operators and developers.", (
        ("API docs", "Internal placeholder: /docs/api"),
        ("Trace docs", "Internal placeholder: /docs/trace"),
        ("Evidence docs", "Internal placeholder: /docs/evidence"),
        ("Runtime profiles docs", "Internal placeholder: /docs/runtime-profiles"),
        ("Developer API docs", "Internal placeholder: /docs/developer-api"),
        ("Security docs", "Internal placeholder: /docs/security"),
        ("Operations docs", "Internal placeholder: /docs/operations"),
    ))
