from __future__ import annotations

from bastion_ui.theme.tokens import BASTION_BORDER, BITCOIN_ORANGE

CARD = {
    "border": f"1px solid {BASTION_BORDER}",
    "border_radius": "18px",
    "padding": "1.25rem",
    "background": "white",
    "box_shadow": "0 10px 30px rgba(17,17,17,0.04)",
}

SAFETY_CARD = {
    **CARD,
    "border_left": f"4px solid {BITCOIN_ORANGE}",
}

CONSOLE_CARD = {
    **CARD,
    "background": "#111111",
    "color": "white",
    "border": "1px solid rgba(255,255,255,0.12)",
}
