from __future__ import annotations

import reflex as rx

from bastion_ui.components.wow._shared import wow_card


def trace_story_mode() -> rx.Component:
    return wow_card("Trace Story Mode", "What is known: backend evidence when available", "What is uncertain: unavailable panels remain visible", "What evidence supports this: evidence refs when present", "What limitations apply: advisory-only", "What an operator should review manually: provider disagreement and source quality")
