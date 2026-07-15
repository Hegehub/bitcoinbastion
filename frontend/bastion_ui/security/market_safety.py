from __future__ import annotations

MARKET_SAFETY_COPY = (
    "Market intelligence is advisory-only. Not financial advice. Not a trading "
    "recommendation. Signals may be incomplete, stale, degraded, or wrong. "
    "Always verify using independent sources. Bitcoin Bastion does not custody "
    "funds and does not execute trades."
)

MARKET_NO_CUSTODY_COPY = (
    "Display-only overview. No seed phrase input, private key input, wallet file "
    "upload, trading API key input, exchange secret input, or automatic trade "
    "execution is supported."
)

MARKET_FORBIDDEN_CLAIM_PARTS: tuple[tuple[str, str] | tuple[str, str, str], ...] = (
    ("guaranteed", "profit"),
    ("guaranteed", "signal"),
    ("buy", "now"),
    ("sell", "now"),
    ("safe", "trade"),
    ("risk", "free"),
    ("financial", "advice"),
    ("approved", "trade"),
    ("certain", "outcome"),
)


def market_safety_claims() -> tuple[str, ...]:
    return tuple(MARKET_SAFETY_COPY.split(". "))
