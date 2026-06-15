from __future__ import annotations

import reflex as rx

from bastion_ui.components.wow.trace_radar import trace_radar
from bastion_ui.components.wow.trace_story_mode import trace_story_mode
from bastion_ui.components.wow.privacy_exposure_lens import privacy_exposure_lens
from bastion_ui.components.wow.provider_trust_matrix import provider_trust_matrix
from bastion_ui.components.console.dashboard_shell import dashboard_shell
from bastion_ui.components.ui.card import card
from bastion_ui.components.ui.safety_banner import safety_banner


def console_trace_page() -> rx.Component:
    return dashboard_shell("Console Trace", rx.vstack(
        safety_banner("trace"),
        trace_radar(),
        trace_story_mode(),
        privacy_exposure_lens(),
        provider_trust_matrix(),
        card(rx.text("Trace module overview. Recent reports are unavailable until backend data is connected."), rx.link("Open Trace", href="/trace"), rx.link("Check Bitcoin Address", href="/check"), title="Trace Module"),
        card(rx.text("Trace remains advisory-only and cannot be used as a legal verdict or consensus proof."), title="Trace Limitations"),
        spacing="4",
        width="100%",
    ))
