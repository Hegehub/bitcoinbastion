from __future__ import annotations

from bastion_ui.app import PUBLIC_ROUTE_REGISTRATIONS
from bastion_ui.security.report_validation import validate_report_id


def test_trace_report_dynamic_routes_registered() -> None:
    routes = {route for route, _, _ in PUBLIC_ROUTE_REGISTRATIONS}
    assert "/trace/[report_id]" in routes
    assert "/trace/[report_id]/proof-packet" in routes


def test_invalid_report_id_is_rejected_safely() -> None:
    for value in (
        "",
        "../secret",
        "..\\secret",
        "<script>alert(1)</script>",
        "javascript:1",
        "file:/tmp/x",
        "data:text/plain,x",
    ):
        result = validate_report_id(value)
        assert result.ok is False
        assert result.error == "Invalid Trace report identifier."


def test_valid_report_id_is_preserved() -> None:
    result = validate_report_id("report_2026-06-18_abc123")
    assert result.ok is True
    assert result.value == "report_2026-06-18_abc123"


def test_trace_report_state_marks_partial_panel_failures() -> None:
    source = __import__("pathlib").Path("bastion_ui/state/trace_report_state.py").read_text()
    assert "Some Trace report panels could not be loaded." in source
    assert "self.has_degraded_data = True" in source
