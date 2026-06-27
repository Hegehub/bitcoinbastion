from __future__ import annotations

from bastion_ui.navigation import (
    COMMAND_PALETTE_ACTIONS,
    STALE_CANONICAL_ROUTES,
    filter_command_actions,
)
from bastion_ui.routes.registry import ALL_REFLEX_ROUTES

REQUIRED_ACTION_ROUTES = {
    "Open Trace": "/trace",
    "Check Bitcoin Address": "/check",
    "Open Evidence": "/evidence",
    "Open Status": "/status",
    "Open Console": "/console",
    "Open Market Intelligence": "/console/market-intelligence",
    "Open Time Machine": "/console/time-machine",
    "Open Sovereign Grid": "/console/sovereign-grid",
    "Open Audit Log": "/console/audit",
}
FORBIDDEN_PARTS = [
    ("clean", "address"),
    ("dirty", "address"),
    ("criminal", "address"),
    ("guaranteed", "safe"),
    ("approved", "payment"),
    ("verified", "illicit"),
]
RISKY_COMMAND_WORDS = ("execute treasury", "sign transaction", "broadcast transaction")


def test_command_palette_contains_required_actions_and_no_stale_routes() -> None:
    by_title = {action.title: action.route for action in COMMAND_PALETTE_ACTIONS}
    for title, route in REQUIRED_ACTION_ROUTES.items():
        assert by_title[title] == route
    assert by_title["Open Policy Engine"] == "/console/policy"
    assert STALE_CANONICAL_ROUTES.isdisjoint({action.route for action in COMMAND_PALETTE_ACTIONS})


def test_command_routes_are_registered_or_dynamic_trace_helpers() -> None:
    registered = set(ALL_REFLEX_ROUTES)
    dynamic_helpers = {"/trace/{report_id}", "/trace/{report_id}/proof-packet"}
    for action in COMMAND_PALETTE_ACTIONS:
        assert action.route in registered or action.route in dynamic_helpers


def test_dynamic_trace_commands_require_input_and_safety_notes_exist() -> None:
    by_id = {action.id: action for action in COMMAND_PALETTE_ACTIONS}
    assert by_id["open-trace-report"].requires_input is True
    assert by_id["open-proof-packet"].requires_input is True
    assert by_id["open-trace"].safety_note
    assert by_id["open-evidence"].safety_note
    assert by_id["open-policy"].safety_note


def test_command_palette_filter_searches_title_and_route() -> None:
    assert any(action.title == "Open Trace" for action in filter_command_actions("trace"))
    assert any(
        action.route == "/console/time-machine" for action in filter_command_actions("time-machine")
    )


def test_command_labels_are_safe_and_do_not_expose_risky_execution() -> None:
    text = "\n".join(
        f"{action.title} {action.route} {action.description} {action.safety_note or ''}"
        for action in COMMAND_PALETTE_ACTIONS
    ).lower()
    for left, right in FORBIDDEN_PARTS:
        assert f"{left} {right}" not in text
    for word in RISKY_COMMAND_WORDS:
        assert word not in text
