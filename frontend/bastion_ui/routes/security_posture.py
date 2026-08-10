from __future__ import annotations

import reflex as rx

from bastion_ui.components.security.access_required import access_required_shell
from bastion_ui.routes._shared import public_page
from bastion_ui.state.security_shell_state import SecurityShellState


def security_posture_page() -> rx.Component:
    return public_page(
        "Protected security posture",
        rx.button("Check Access", on_click=SecurityShellState.refresh_posture, id="security-retry"),
        rx.text("Security state: ", SecurityShellState.lifecycle, id="security-lifecycle"),
        rx.cond(
            SecurityShellState.protected_visible,
            rx.text("Backend-authorized protected posture", id="protected-content"),
            access_required_shell(
                SecurityShellState.denial_heading, SecurityShellState.denial_detail
            ),
        ),
        subtitle="Frontend eligibility is advisory; backend authorization always wins.",
    )
