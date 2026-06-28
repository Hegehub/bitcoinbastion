from __future__ import annotations

from bastion_ui.components.console.market_intelligence_panel import MARKET_INTELLIGENCE_SAFETY_COPY


def test_market_intelligence_safety_copy() -> None:
    assert "Market intelligence is advisory-only" in MARKET_INTELLIGENCE_SAFETY_COPY
    assert "not financial advice" in MARKET_INTELLIGENCE_SAFETY_COPY
    assert "provider-dependent" in MARKET_INTELLIGENCE_SAFETY_COPY
