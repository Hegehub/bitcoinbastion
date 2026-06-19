from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.components.safety.advisory_notice import advisory_notice
from bastion_ui.components.safety.no_custody_notice import no_custody_notice


def trace_safety_banner() -> rx.Component:
    return cast(rx.Component, rx.vstack(advisory_notice(), no_custody_notice(), width="100%"))
