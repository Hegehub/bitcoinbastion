from __future__ import annotations

_FORBIDDEN_PAIRS = (
    ("clean", "address"),
    ("dirty", "address"),
    ("criminal", "address"),
    ("guaranteed", "safe"),
    ("approved", "payment"),
    ("verified", "illicit"),
)

FORBIDDEN_USER_FACING_TERMS = tuple(f"{left} {right}" for left, right in _FORBIDDEN_PAIRS)

SAFE_TRACE_TERMS = (
    "limited evidence",
    "manual review recommended",
    "provider disagreement",
    "insufficient evidence",
    "elevated risk band",
    "low confidence",
    "not legal verification",
    "not Bitcoin consensus proof",
    "advisory-only",
)

SAFE_MARKET_TERMS = (
    "informational only",
    "not financial advice",
    "provider-dependent",
    "stale data visible",
)

SAFE_POLICY_TERMS = (
    "human operator review required",
    "preview only",
    "no auto-execution",
    "manual approval boundary",
)

_REPLACEMENTS = dict(
    zip(
        FORBIDDEN_USER_FACING_TERMS,
        (
            "limited evidence",
            "elevated risk band",
            "manual review recommended",
            "low confidence",
            "manual review recommended",
            "provider disagreement",
        ),
        strict=True,
    )
)


def contains_forbidden_wording(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in FORBIDDEN_USER_FACING_TERMS)


def sanitize_visual_label(text: str) -> str:
    sanitized = text
    lowered = sanitized.lower()
    for forbidden, replacement in _REPLACEMENTS.items():
        if forbidden in lowered:
            sanitized = sanitized.replace(forbidden, replacement)
            sanitized = sanitized.replace(forbidden.title(), replacement.title())
            lowered = sanitized.lower()
    return sanitized
