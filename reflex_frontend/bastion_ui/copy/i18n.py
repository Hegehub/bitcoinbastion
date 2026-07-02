from __future__ import annotations

DEFAULT_LOCALE = "en"

SAFETY_COPY: dict[str, str] = {
    "no_custody": "Bitcoin Bastion never asks for seed phrases, private keys, wallet files, or signing material.",
    "advisory_only": "Trace, Market, Evidence, and Console views are informational and advisory only.",
    "market_not_advice": "Market Intelligence is historical context and not financial advice.",
    "operator_review": "Risk-sensitive actions require explicit operator review outside the frontend preview layer.",
}

__all__ = ["DEFAULT_LOCALE", "SAFETY_COPY"]
