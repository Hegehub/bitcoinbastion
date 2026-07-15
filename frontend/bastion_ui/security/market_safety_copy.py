from __future__ import annotations

MARKET_TIME_MACHINE_SAFETY_COPY = (
    "Market intelligence is advisory-only. It is not financial advice, not a trading "
    "instruction, and not a guarantee of future price movement. Historical similarity "
    "is advisory-only. Signals require operator review. Provider disagreement and "
    "stale data reduce confidence."
)

MARKET_TIME_MACHINE_NO_CUSTODY_COPY = (
    "Market pages do not request seed phrases, private keys, wallet files, exchange "
    "API secrets, or signing material. Bitcoin Bastion does not execute trades, sign "
    "transactions, or approve treasury actions from these views."
)

MARKET_FORBIDDEN_PARTS: tuple[tuple[str, str], ...] = (
    ("guaranteed", "profit"),
    ("guaranteed", "signal"),
    ("certain", "prediction"),
    ("risk-free", "trade"),
    ("buy", "now"),
    ("sell", "now"),
    ("approved", "trade"),
    ("perfect", "entry"),
)
