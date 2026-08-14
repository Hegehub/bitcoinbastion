from bastion_ui.theme.tokens import COLOR, FONT_MONO, FONT_SANS

DISPLAY = {
    "font_family": FONT_SANS,
    "font_size": "56px",
    "line_height": "1.05",
    "font_weight": "800",
}
H1 = {"font_family": FONT_SANS, "font_size": "42px", "line_height": "1.12", "font_weight": "750"}
H2 = {"font_family": FONT_SANS, "font_size": "32px", "line_height": "1.18", "font_weight": "700"}
H3 = {"font_family": FONT_SANS, "font_size": "24px", "line_height": "1.25", "font_weight": "650"}
H4 = {"font_family": FONT_SANS, "font_size": "20px", "line_height": "1.3", "font_weight": "650"}
BODY = {"font_family": FONT_SANS, "font_size": "16px", "line_height": "1.65"}
BODY_MUTED = {**BODY, "color": COLOR["text_secondary"]}
SMALL = {"font_family": FONT_SANS, "font_size": "14px", "line_height": "1.55"}
CAPTION = {
    "font_family": FONT_SANS,
    "font_size": "13px",
    "line_height": "1.5",
    "color": COLOR["text_secondary"],
}
MONO = {"font_family": FONT_MONO, "font_size": "14px", "line_height": "1.6"}
CODE = {
    **MONO,
    "background": "rgba(255,255,255,0.06)",
    "padding": "2px 6px",
    "border_radius": "6px",
}
METRIC = {"font_family": FONT_SANS, "font_size": "34px", "line_height": "1.1", "font_weight": "750"}
LABEL = {"font_family": FONT_SANS, "font_size": "14px", "line_height": "1.4", "font_weight": "650"}
