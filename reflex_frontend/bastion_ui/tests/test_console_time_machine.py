from __future__ import annotations

from bastion_ui.components.console.time_machine_panel import TIME_MACHINE_SAFETY_COPY


def test_time_machine_safety_copy() -> None:
    assert "Historical similarity is not prediction" in TIME_MACHINE_SAFETY_COPY
    assert "not future certainty" in TIME_MACHINE_SAFETY_COPY
    assert "not financial advice" in TIME_MACHINE_SAFETY_COPY
