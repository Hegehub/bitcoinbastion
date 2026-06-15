from __future__ import annotations

import reflex as rx

from bastion_ui.components.wow._shared import wow_card


def human_confirmation_firewall() -> rx.Component:
    return wow_card("Human Confirmation Firewall", "action summary: draft preview", "risk summary: operator review required", "affected domain: policy/treasury preview", "required human review step: acknowledge limitations", "Allowed labels: Review draft · Acknowledge limitations · Request operator approval · Create draft only", "Final action button is disabled by default.")
