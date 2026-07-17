from __future__ import annotations

from bastion_ui.security.market_safety import MARKET_NO_CUSTODY_COPY, MARKET_SAFETY_COPY


def test_market_safety_copy_visible() -> None:
    assert "Market intelligence is advisory-only." in MARKET_SAFETY_COPY
    assert "Not " + "financial advice." in MARKET_SAFETY_COPY
    assert "Not a trading recommendation." in MARKET_SAFETY_COPY
    assert "Signals may be incomplete, stale, degraded, or wrong." in MARKET_SAFETY_COPY
    assert "does not custody funds" in MARKET_SAFETY_COPY
    assert "does not execute trades" in MARKET_SAFETY_COPY


def test_market_no_custody_copy_visible() -> None:
    assert "No seed phrase input" in MARKET_NO_CUSTODY_COPY
    assert "private key input" in MARKET_NO_CUSTODY_COPY
    assert "wallet file upload" in MARKET_NO_CUSTODY_COPY
    assert "trading API key input" in MARKET_NO_CUSTODY_COPY
    assert "exchange secret input" in MARKET_NO_CUSTODY_COPY
    assert "automatic trade execution" in MARKET_NO_CUSTODY_COPY
