from __future__ import annotations

from bastion_ui.theme.tokens import (
    BASTION_BG,
    BASTION_BG_SOFT,
    BASTION_BORDER,
    BASTION_DANGER,
    BASTION_GRAPHITE,
    BASTION_TEXT,
    BASTION_TEXT_MUTED,
    BITCOIN_ORANGE,
)

PAGE = {
    "background": BASTION_BG,
    "color": BASTION_TEXT,
    "min_height": "100vh",
}

CARD = {
    "background": BASTION_GRAPHITE,
    "border": f"1px solid {BASTION_BORDER}",
    "border_radius": "16px",
    "padding": "24px",
}

PANEL = {
    **CARD,
    "box_shadow": "0 18px 50px rgba(0, 0, 0, 0.35)",
}

CONSOLE_PANEL = {
    **PANEL,
    "background": BASTION_BG_SOFT,
}

SAFETY_CARD = {
    "background": BASTION_BG_SOFT,
    "border": "1px solid #F59E0B",
    "border_radius": "16px",
    "padding": "16px",
}

SECTION = {
    "padding": "48px 0",
    "width": "100%",
}

FOCUS_RING = {
    "_focus_visible": {"outline": f"3px solid {BITCOIN_ORANGE}", "outline_offset": "2px"},
}

BUTTON_PRIMARY = {
    "background": BITCOIN_ORANGE,
    "color": "#111827",
    "border": f"1px solid {BITCOIN_ORANGE}",
    "border_radius": "12px",
    "font_weight": "700",
}

BUTTON_SECONDARY = {
    "background": "transparent",
    "color": BASTION_TEXT,
    "border": f"1px solid {BASTION_BORDER}",
    "border_radius": "12px",
}

BUTTON_GHOST = {
    "background": "transparent",
    "color": BASTION_TEXT_MUTED,
    "border": "1px solid transparent",
    "border_radius": "12px",
}

BADGE = {
    "background": "transparent",
    "border_radius": "999px",
    "padding": "4px 10px",
    "font_weight": "600",
}

INPUT = {
    "background": BASTION_BG_SOFT,
    "color": BASTION_TEXT,
    "border": f"1px solid {BASTION_BORDER}",
    "border_radius": "12px",
    "width": "100%",
}

ERROR_TEXT = {"color": BASTION_DANGER}
