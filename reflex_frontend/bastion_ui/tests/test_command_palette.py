from __future__ import annotations

from bastion_ui.navigation import (
    COMMAND_PALETTE_ACTIONS,
    STALE_CANONICAL_ROUTES,
    filter_command_actions,
)

REQUIRED_ACTIONS = [
    "Open Trace",
    "Check Bitcoin Address",
    "Open Evidence",
    "Open Console",
    "Open Market Intelligence",
    "Open Time Machine",
    "Open Sovereign Grid",
    "Open Policy Engine",
    "Open Audit Log",
]
FORBIDDEN_PARTS = [
    ("clean", "address"),
    ("dirty", "address"),
    ("criminal", "address"),
    ("guaranteed", "safe"),
    ("approved", "payment"),
    ("verified", "illicit"),
]


def test_command_palette_contains_required_actions_and_no_stale_routes() -> None:
    titles = {action.title for action in COMMAND_PALETTE_ACTIONS}
    routes = {action.route for action in COMMAND_PALETTE_ACTIONS}
    for title in REQUIRED_ACTIONS:
        assert title in titles
    assert STALE_CANONICAL_ROUTES.isdisjoint(routes)


def test_dynamic_trace_commands_require_input_and_safety_notes_exist() -> None:
    by_id = {action.id: action for action in COMMAND_PALETTE_ACTIONS}
    assert by_id["open-trace-report"].requires_input is True
    assert by_id["open-proof-packet"].requires_input is True
    assert by_id["open-trace"].safety_note
    assert by_id["open-evidence"].safety_note


def test_command_palette_filter_searches_title_and_route() -> None:
    assert any(action.title == "Open Trace" for action in filter_command_actions("trace"))
    assert any(
        action.route == "/console/time-machine" for action in filter_command_actions("time-machine")
    )


def test_forbidden_wording_absent_from_command_metadata() -> None:
    text = "\n".join(
        f"{action.title} {action.route} {action.description} {action.safety_note or ''}"
        for action in COMMAND_PALETTE_ACTIONS
    ).lower()
    for left, right in FORBIDDEN_PARTS:
        assert f"{left} {right}" not in text
