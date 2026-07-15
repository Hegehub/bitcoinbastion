from __future__ import annotations

from bastion_ui.components.console.sovereign_grid_panel import SOVEREIGN_GRID_SAFETY_COPY


def test_sovereign_grid_does_not_claim_forbidden_capabilities() -> None:
    lowered = SOVEREIGN_GRID_SAFETY_COPY.lower()
    assert "frontend readiness view only" in lowered
    assert "does not create distributed backend mesh" in lowered
    assert "mining support" in lowered
    assert "fake network status" in lowered
