from __future__ import annotations

from pathlib import Path

from bastion_ui.navigation import COMMAND_PALETTE_ACTIONS, search_command_actions

REQUIRED_ACTIONS = {
    "Open Trace",
    "Check Bitcoin Address",
    "Open Evidence",
    "Open Console",
    "Open Market Intelligence",
    "Open Time Machine",
    "Open Sovereign Grid",
    "Open Policy Engine",
    "Open Audit Log",
}

BLOCKED_PHRASES = (
    "clean" + " address",
    "dirty" + " address",
    "criminal" + " address",
    "guaranteed" + " safe",
    "approved" + " payment",
    "verified" + " illicit",
)


def test_command_palette_contains_required_actions() -> None:
    titles = {action.title for action in COMMAND_PALETTE_ACTIONS}
    assert REQUIRED_ACTIONS <= titles


def test_command_palette_avoids_stale_canonical_routes() -> None:
    routes = {action.route for action in COMMAND_PALETTE_ACTIONS}
    assert "/products" not in routes
    assert "/self-host" not in routes


def test_dynamic_trace_commands_require_input() -> None:
    by_id = {action.id: action for action in COMMAND_PALETTE_ACTIONS}
    assert by_id["open-trace-report"].requires_input is True
    assert by_id["open-proof-packet"].requires_input is True
    assert "{report_id}" in by_id["open-trace-report"].route
    assert "{report_id}" in by_id["open-proof-packet"].route


def test_trace_and_evidence_commands_have_safety_notes() -> None:
    by_id = {action.id: action for action in COMMAND_PALETTE_ACTIONS}
    assert by_id["open-trace"].safety_note
    assert by_id["open-evidence"].safety_note
    assert by_id["open-proof-packet"].safety_note


def test_command_search_filters_by_title_and_route() -> None:
    assert [action.title for action in search_command_actions("Trace")]
    assert [action.title for action in search_command_actions("/console/time-machine")] == [
        "Open Time Machine"
    ]


def test_forbidden_wording_absent_from_navigation_modules() -> None:
    root = Path(__file__).resolve().parents[1]
    files = [root / "navigation.py", root / "components" / "layout" / "command_palette.py"]
    for path in files:
        text = path.read_text().casefold()
        for phrase in BLOCKED_PHRASES:
            assert phrase not in text
