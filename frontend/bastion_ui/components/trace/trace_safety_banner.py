from __future__ import annotations

import reflex as rx

from bastion_ui.components.ui.alert import alert
from bastion_ui.security.safety_copy import TRACE_PUBLIC_SAFETY_COPY


def trace_safety_banner() -> rx.Component:
    return alert(TRACE_PUBLIC_SAFETY_COPY, "advisory")
