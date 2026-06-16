from bastion_ui.theme.tokens import (
    BASTION_BG,
    BASTION_GRAPHITE,
    BASTION_PANEL,
    BASTION_PANEL_SOFT,
    BASTION_TEXT,
    BASTION_TEXT_MUTED,
    BITCOIN_ORANGE,
    BORDER_DEFAULT,
    BORDER_WARNING,
    RADIUS_LG,
    RADIUS_MD,
    SHADOW_FOCUS,
    SHADOW_PANEL,
)

PAGE = {"background": BASTION_BG, "color": BASTION_TEXT, "min_height": "100vh"}
CONTAINER = {"width": "100%", "max_width": "1180px", "margin": "0 auto", "padding": "0 24px"}
SECTION = {"padding": "72px 0"}
CARD = {"border": BORDER_DEFAULT, "border_radius": RADIUS_LG, "padding": "24px"}
CARD_HOVER = {**CARD, "transition": "border-color 180ms ease, transform 180ms ease"}
PANEL = {**CARD, "background": BASTION_PANEL, "box_shadow": SHADOW_PANEL}
CONSOLE_PANEL = {**PANEL, "background": BASTION_PANEL_SOFT}
SAFETY_CARD = {"border": BORDER_WARNING, "border_radius": RADIUS_LG, "padding": "16px"}
INPUT = {
    "border": BORDER_DEFAULT,
    "border_radius": RADIUS_MD,
    "background": BASTION_GRAPHITE,
    "color": BASTION_TEXT,
    "padding": "12px 14px",
}
BUTTON_PRIMARY = {
    "background": BITCOIN_ORANGE,
    "color": BASTION_GRAPHITE,
    "border": f"1px solid {BITCOIN_ORANGE}",
}
BUTTON_SECONDARY = {"background": BASTION_PANEL, "color": BASTION_TEXT, "border": BORDER_DEFAULT}
BUTTON_GHOST = {"background": "transparent", "color": BASTION_TEXT, "border": BORDER_DEFAULT}
BADGE = {"border": BORDER_DEFAULT, "border_radius": "999px", "padding": "4px 10px"}
MONO_TEXT = {"font_family": "JetBrains Mono, ui-monospace, monospace"}
LINK = {"color": BITCOIN_ORANGE, "text_decoration": "none"}
FOCUS_RING = {"_focus_visible": {"box_shadow": SHADOW_FOCUS, "outline": "none"}}
RISK_INDICATOR = {"display": "inline-flex", "gap": "8px", "align_items": "center"}
MUTED_TEXT = {"color": BASTION_TEXT_MUTED}
