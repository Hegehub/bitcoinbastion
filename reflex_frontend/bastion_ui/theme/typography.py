from bastion_ui.theme.tokens import BASTION_TEXT, BASTION_TEXT_MUTED, FONT_MONO, FONT_SANS

DISPLAY = {
    "font_family": FONT_SANS,
    "font_size": "clamp(40px, 7vw, 72px)",
    "line_height": "1.05",
    "font_weight": "800",
    "color": BASTION_TEXT,
}

H1 = {"font_family": FONT_SANS, "font_size": "40px", "line_height": "1.15", "font_weight": "800"}
H2 = {"font_family": FONT_SANS, "font_size": "32px", "line_height": "1.2", "font_weight": "750"}
H3 = {"font_family": FONT_SANS, "font_size": "24px", "line_height": "1.25", "font_weight": "700"}
H4 = {"font_family": FONT_SANS, "font_size": "20px", "line_height": "1.3", "font_weight": "700"}
BODY = {"font_family": FONT_SANS, "font_size": "16px", "line_height": "1.65", "color": BASTION_TEXT}
BODY_MUTED = {**BODY, "color": BASTION_TEXT_MUTED}
SMALL = {"font_family": FONT_SANS, "font_size": "14px", "line_height": "1.5"}
CAPTION = {"font_family": FONT_SANS, "font_size": "13px", "line_height": "1.45"}
MONO = {"font_family": FONT_MONO, "font_size": "14px", "line_height": "1.5"}
CODE = {**MONO, "padding": "2px 6px", "border_radius": "8px"}
METRIC = {"font_family": FONT_SANS, "font_size": "28px", "line_height": "1.1", "font_weight": "800"}
LABEL = {"font_family": FONT_SANS, "font_size": "14px", "line_height": "1.4", "font_weight": "700"}
