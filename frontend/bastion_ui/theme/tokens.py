"""Canonical Bitcoin-first visual tokens shared by both color modes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True)
class ThemePalette:
    background: str
    elevated: str
    surface: str
    glass: str
    matte: str
    border: str
    separator: str
    text: str
    text_secondary: str
    text_muted: str
    brand: str
    brand_hover: str
    brand_pressed: str
    focus: str
    success: str
    warning: str
    error: str
    information: str
    disabled: str


DARK = ThemePalette(
    background="#060606",
    elevated="#11100E",
    surface="#181614",
    glass="rgba(28, 25, 22, 0.72)",
    matte="rgba(24, 22, 20, 0.94)",
    border="#3A342D",
    separator="#292520",
    text="#FFF9F1",
    text_secondary="#DDD3C7",
    text_muted="#A89E92",
    brand="#F7931A",
    brand_hover="#FFA33B",
    brand_pressed="#D97706",
    focus="#FFB454",
    success="#35B779",
    warning="#EAB308",
    error="#EF5B5B",
    information="#8B9E7D",
    disabled="#746B61",
)
LIGHT = ThemePalette(
    background="#F7F3EC",
    elevated="#FFFDF8",
    surface="#F0E9DE",
    glass="rgba(255, 253, 248, 0.76)",
    matte="rgba(250, 247, 241, 0.95)",
    border="#C8BFB2",
    separator="#DDD4C8",
    text="#211E1A",
    text_secondary="#514A42",
    text_muted="#756C62",
    brand="#C76500",
    brand_hover="#A94F00",
    brand_pressed="#853D00",
    focus="#9D4800",
    success="#16794B",
    warning="#8A6500",
    error="#B52F36",
    information="#536D48",
    disabled="#9B9288",
)


class MaterialLevel(StrEnum):
    SOLID = "SOLID"
    MATTE = "MATTE"
    GLASS_SUBTLE = "GLASS_SUBTLE"
    GLASS_ELEVATED = "GLASS_ELEVATED"
    GLASS_OVERLAY = "GLASS_OVERLAY"


# CSS-variable roles are the canonical runtime interface. Color-mode selection is
# handled by Reflex/Radix before components render; it does not touch domain State.
COLOR = {name: f"var(--bb-{name.replace('_', '-')})" for name in ThemePalette.__annotations__}

SPACE = {
    1: "4px",
    2: "8px",
    3: "12px",
    4: "16px",
    5: "20px",
    6: "24px",
    8: "32px",
    10: "40px",
    12: "48px",
}
RADIUS = {"sm": "8px", "md": "12px", "lg": "16px", "xl": "22px", "pill": "999px"}
SHADOW = {
    "low": "0 8px 24px rgba(0,0,0,.14)",
    "medium": "0 18px 44px rgba(0,0,0,.22)",
    "high": "0 24px 64px rgba(0,0,0,.28)",
}
BLUR = {"subtle": "10px", "elevated": "16px", "overlay": "20px"}
MOTION = {
    "instant": "0ms",
    "fast": "120ms",
    "normal": "180ms",
    "slow": "320ms",
    "ease_out": "cubic-bezier(.16,1,.3,1)",
    "ease_standard": "cubic-bezier(.4,0,.2,1)",
}
LAYER = {"base": 0, "sticky": 20, "popover": 30, "overlay": 40, "modal": 50, "toast": 60}
FONT = {
    "sans": "Inter, ui-sans-serif, system-ui, -apple-system, sans-serif",
    "mono": "JetBrains Mono, ui-monospace, SFMono-Regular, monospace",
}

# Compatibility aliases: shared primitives should prefer COLOR roles.
BITCOIN_ORANGE = DARK.brand
BASTION_BLACK = DARK.background
BASTION_GRAPHITE = DARK.surface
BASTION_PANEL = DARK.surface
BASTION_PANEL_SOFT = DARK.elevated
BASTION_GRAY = DARK.disabled
BASTION_BORDER = DARK.border
BASTION_BG = DARK.background
BASTION_BG_SOFT = DARK.elevated
BASTION_DANGER = DARK.error
BASTION_WARNING = DARK.warning
BASTION_SUCCESS = DARK.success
BASTION_BLUE = "#3B82F6"  # legacy/data-series compatibility only; never a brand role
BASTION_INFO = DARK.information
BASTION_TEXT = DARK.text
BASTION_TEXT_MUTED = DARK.text_secondary
BASTION_TEXT_DIM = DARK.text_muted
BASTION_NEUTRAL = DARK.disabled
RISK_LOW, RISK_MEDIUM, RISK_HIGH, RISK_UNKNOWN = (
    BASTION_SUCCESS,
    BASTION_WARNING,
    BASTION_DANGER,
    BASTION_NEUTRAL,
)
EVIDENCE_STRONG, EVIDENCE_PARTIAL, EVIDENCE_WEAK, EVIDENCE_UNKNOWN = (
    RISK_LOW,
    RISK_MEDIUM,
    RISK_HIGH,
    RISK_UNKNOWN,
)
SPACE_1, SPACE_2, SPACE_3, SPACE_4, SPACE_5, SPACE_6, SPACE_8, SPACE_10, SPACE_12 = (
    SPACE[x] for x in (1, 2, 3, 4, 5, 6, 8, 10, 12)
)
RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_XL = (RADIUS[x] for x in ("sm", "md", "lg", "xl"))
SHADOW_PANEL, SHADOW_FOCUS = (
    SHADOW["medium"],
    "0 0 0 3px color-mix(in srgb, var(--bb-focus) 35%, transparent)",
)
BORDER_DEFAULT, BORDER_WARNING, BORDER_DANGER = (
    f"1px solid {BASTION_BORDER}",
    f"1px solid {BASTION_WARNING}",
    f"1px solid {BASTION_DANGER}",
)
FONT_SANS, FONT_MONO = FONT["sans"], FONT["mono"]
Z_BASE, Z_HEADER, Z_OVERLAY, Z_MODAL = (
    LAYER["base"],
    LAYER["sticky"],
    LAYER["overlay"],
    LAYER["modal"],
)
BREAKPOINT_MOBILE, BREAKPOINT_TABLET, BREAKPOINT_DESKTOP, BREAKPOINT_WIDE = (
    "0px",
    "768px",
    "1024px",
    "1280px",
)
RISK_STATES = {
    "low": {"color": RISK_LOW, "label": "Low risk band"},
    "medium": {"color": RISK_MEDIUM, "label": "Elevated risk band"},
    "high": {"color": RISK_HIGH, "label": "High risk band"},
    "unknown": {"color": RISK_UNKNOWN, "label": "Unknown risk band"},
}
DATA_STATES = {
    "available": {"color": BASTION_SUCCESS, "label": "Available"},
    "degraded": {"color": BASTION_WARNING, "label": "Degraded"},
    "stale": {"color": BASTION_WARNING, "label": "Stale data"},
    "unavailable": {"color": BASTION_DANGER, "label": "Unavailable"},
}
EVIDENCE_STATES = {
    "strong": {"color": EVIDENCE_STRONG, "label": "Strong evidence"},
    "partial": {"color": EVIDENCE_PARTIAL, "label": "Limited evidence"},
    "weak": {"color": EVIDENCE_WEAK, "label": "Low confidence"},
    "unknown": {"color": EVIDENCE_UNKNOWN, "label": "Insufficient evidence"},
}
