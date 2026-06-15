from __future__ import annotations

import reflex as rx

from bastion_ui.components.wow._shared import wow_card

STATUSES = "healthy · degraded · stale · fallback · unavailable · unknown"


def provider_trust_matrix() -> rx.Component:
    return wow_card("Provider Trust Matrix", "provider name · domain · status · confidence · freshness · fallback state · stale data warning · last checked", f"Supported statuses: {STATUSES}")
