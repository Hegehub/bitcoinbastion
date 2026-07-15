from __future__ import annotations

from bastion_ui.components.wow.evidence_chain_viewer import SAFETY_COPY as EVIDENCE_COPY
from bastion_ui.components.wow.market_intelligence_wall import SAFETY_COPY as MARKET_COPY
from bastion_ui.components.wow.policy_simulator_preview import SAFETY_COPY as POLICY_COPY
from bastion_ui.components.wow.trace_radar import SAFETY_COPY as TRACE_COPY


def test_required_wow_safety_copy() -> None:
    assert "Not legal verification" in TRACE_COPY
    assert "Not Bitcoin consensus proof" in TRACE_COPY
    assert "No custody" in TRACE_COPY
    assert "This is not Bitcoin consensus proof" in EVIDENCE_COPY
    assert "not financial advice" in MARKET_COPY
    assert "Human operator review is required" in POLICY_COPY
