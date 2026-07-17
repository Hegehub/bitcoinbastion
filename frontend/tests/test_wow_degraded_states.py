from __future__ import annotations

from bastion_ui.components.wow.degraded_mode_banner import SAFETY_COPY as DEGRADED_COPY
from bastion_ui.components.wow.node_pulse import UNAVAILABLE_COPY
from bastion_ui.services.wow_client import UNAVAILABLE_REASON
from bastion_ui.state.wow_state import SAFE_UNAVAILABLE


def test_wow_degraded_and_unavailable_copy() -> None:
    assert "degraded" in DEGRADED_COPY
    assert "fallback" in DEGRADED_COPY
    assert "unknown" in DEGRADED_COPY
    assert "safe unavailable states" in UNAVAILABLE_COPY


def test_wow_state_defaults_are_unavailable() -> None:
    assert SAFE_UNAVAILABLE["available"] is False
    assert UNAVAILABLE_REASON in SAFE_UNAVAILABLE["reason"]
