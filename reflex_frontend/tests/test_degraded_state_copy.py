from __future__ import annotations

from bastion_ui.components.ui.fallback_mode_notice import FALLBACK_MODE_COPY
from bastion_ui.i18n.translations import translate
from bastion_ui.security.safety_copy import DEGRADED_DATA, STALE_DATA


def test_degraded_state_copy_exists() -> None:
    assert "Degraded data" in DEGRADED_DATA
    assert "Stale data" in STALE_DATA
    assert "Fallback mode" in FALLBACK_MODE_COPY
    assert translate("degraded.provider_unavailable", "en")
    assert translate("degraded.partial_result", "ru")
