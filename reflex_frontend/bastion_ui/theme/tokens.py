BITCOIN_ORANGE = "#F7931A"
BASTION_BLACK = "#050505"
BASTION_GRAPHITE = "#111827"
BASTION_GRAY = "#6B7280"
BASTION_BORDER = "#1F2937"
BASTION_BG = "#020617"
BASTION_BG_SOFT = "#0F172A"
BASTION_DANGER = "#EF4444"
<<<<<<< HEAD
BASTION_INFO = "#3B82F6"
BASTION_NEUTRAL = "#737373"

RISK_LOW = "#22C55E"
RISK_MEDIUM = "#F59E0B"
RISK_HIGH = "#EF4444"
RISK_UNKNOWN = "#737373"

EVIDENCE_STRONG = "#22C55E"
EVIDENCE_PARTIAL = "#F59E0B"
EVIDENCE_WEAK = "#EF4444"
EVIDENCE_UNKNOWN = "#737373"

# Backward-compatible aliases for the scaffold shell.
BASTION_BG = BASTION_BLACK
BASTION_GRAY = BASTION_TEXT_MUTED

SPACE_1 = "4px"
SPACE_2 = "8px"
SPACE_3 = "12px"
SPACE_4 = "16px"
SPACE_5 = "20px"
SPACE_6 = "24px"
SPACE_8 = "32px"
SPACE_10 = "40px"
SPACE_12 = "48px"

RADIUS_SM = "8px"
RADIUS_MD = "12px"
RADIUS_LG = "16px"
RADIUS_XL = "24px"

SHADOW_PANEL = "0 18px 50px rgba(0, 0, 0, 0.35)"
SHADOW_FOCUS = "0 0 0 3px rgba(247, 147, 26, 0.35)"

BORDER_DEFAULT = f"1px solid {BASTION_BORDER}"
BORDER_WARNING = f"1px solid {BASTION_WARNING}"
BORDER_DANGER = f"1px solid {BASTION_DANGER}"

FONT_SANS = "Inter, ui-sans-serif, system-ui, sans-serif"
FONT_MONO = "JetBrains Mono, ui-monospace, SFMono-Regular, monospace"

Z_BASE = 0
Z_HEADER = 20
Z_OVERLAY = 40
Z_MODAL = 50

BREAKPOINT_MOBILE = "0px"
BREAKPOINT_TABLET = "768px"
BREAKPOINT_DESKTOP = "1024px"
BREAKPOINT_WIDE = "1280px"

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
=======
BASTION_WARNING = "#F59E0B"
BASTION_SUCCESS = "#22C55E"
BASTION_BLUE = "#3B82F6"
>>>>>>> origin/main
