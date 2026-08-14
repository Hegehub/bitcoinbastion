from __future__ import annotations

from bastion_ui.theme.materials import material_style
from bastion_ui.theme.tokens import COLOR, MOTION, RADIUS, SHADOW, SPACE, MaterialLevel

PAGE = {
    "background": COLOR["background"],
    "color": COLOR["text"],
    "min_height": "100vh",
    "font_family": "Inter, ui-sans-serif, system-ui, sans-serif",
}
CARD = {**material_style(MaterialLevel.MATTE), "border_radius": RADIUS["lg"], "padding": SPACE[6]}
PANEL = {
    **material_style(MaterialLevel.GLASS_ELEVATED),
    "border_radius": RADIUS["lg"],
    "padding": SPACE[6],
}
CONSOLE_PANEL = {
    **material_style(MaterialLevel.MATTE),
    "border_radius": RADIUS["md"],
    "padding": SPACE[5],
}
SAFETY_CARD = {
    **material_style(MaterialLevel.SOLID),
    "border": f"1px solid {COLOR['warning']}",
    "border_radius": RADIUS["lg"],
    "padding": SPACE[4],
}
SECTION = {"padding": f"{SPACE[12]} 0", "width": "100%"}
FOCUS_RING = {
    "_focus_visible": {
        "outline": f"3px solid {COLOR['focus']}",
        "outline_offset": "3px",
        "box_shadow": "none",
    }
}
BUTTON_BASE = {
    "border_radius": RADIUS["md"],
    "font_weight": "700",
    "transition": (
        f"background {MOTION['fast']} {MOTION['ease_out']}, "
        f"transform {MOTION['fast']} {MOTION['ease_out']}"
    ),
    "_active": {"transform": "translateY(1px)"},
}
BUTTON_PRIMARY = {
    **BUTTON_BASE,
    "background": COLOR["brand"],
    "color": COLOR["background"],
    "border": f"1px solid {COLOR['brand']}",
    "_hover": {"background": COLOR["brand_hover"]},
}
BUTTON_SECONDARY = {
    **BUTTON_BASE,
    "background": COLOR["matte"],
    "color": COLOR["text"],
    "border": f"1px solid {COLOR['border']}",
    "_hover": {"border_color": COLOR["brand"]},
}
BUTTON_GHOST = {
    **BUTTON_BASE,
    "background": "transparent",
    "color": COLOR["text_secondary"],
    "border": "1px solid transparent",
    "_hover": {"background": COLOR["matte"]},
}
BADGE = {
    "background": COLOR["matte"],
    "border_radius": RADIUS["pill"],
    "padding": f"{SPACE[1]} {SPACE[3]}",
    "font_weight": "600",
}
INPUT = {
    "background": COLOR["matte"],
    "color": COLOR["text"],
    "border": f"1px solid {COLOR['border']}",
    "border_radius": RADIUS["md"],
    "width": "100%",
    **FOCUS_RING,
}
ERROR_TEXT = {"color": COLOR["error"]}
GLASS_NAV = {**material_style(MaterialLevel.GLASS_SUBTLE), "box_shadow": SHADOW["low"]}
