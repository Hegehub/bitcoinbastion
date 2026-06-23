from __future__ import annotations

import pytest

pytest.importorskip("reflex")

from pathlib import Path

from bastion_ui.security.report_id_validation import validate_report_id


def test_trace_report_dynamic_routes_are_registered() -> None:
    app_source = Path(__file__).resolve().parents[1] / "app.py"
    text = app_source.read_text()
    assert 'route="/trace/[report_id]"' in text
    assert 'route="/trace/[report_id]/proof-packet"' in text


def test_invalid_report_id_is_handled_safely() -> None:
    for candidate in (
        "",
        "../secret",
        "..\\secret",
        "<script",
        "javascript:alert(1)",
        "file:x",
        "data:x",
    ):
        result = validate_report_id(candidate)
        assert not result.ok
        assert "Invalid Trace report id" in result.error


def test_plain_report_id_is_allowed() -> None:
    result = validate_report_id("report_123")
    assert result.ok
    assert result.report_id == "report_123"
