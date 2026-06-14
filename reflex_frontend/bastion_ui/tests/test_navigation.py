from bastion_ui.components.layout.command_palette import COMMAND_ACTIONS
from bastion_ui.components.layout.header import NAV_ITEMS


def test_navigation_contains_required_items() -> None:
    labels = {label for label, _href in NAV_ITEMS}
    for label in ("Platform", "Trace", "Evidence", "Status", "Developers", "Operations", "Docs", "Security", "Roadmap"):
        assert label in labels


def test_navigation_uses_current_routes_not_legacy_routes() -> None:
    hrefs = {href for _label, href in NAV_ITEMS}
    assert "/platform" in hrefs
    assert "/operations" in hrefs
    assert "/products" not in hrefs
    assert "/self-host" not in hrefs


def test_command_palette_contains_future_compatible_actions() -> None:
    actions = dict(COMMAND_ACTIONS)
    assert actions["Open Trace"] == "/trace"
    assert actions["Open Trace Report"] == "/trace/{report_id}"
    assert actions["Open Proof Packet"] == "/trace/{report_id}/proof-packet"
    assert actions["Open Console"] == "/console"
    assert actions["Open Console Trace"] == "/console/trace"
    assert actions["Open Console Evidence"] == "/console/evidence"
    assert actions["Open Provider Health"] == "/console/provider-health"
    assert actions["Open Time Machine"] == "/console/time-machine"
    assert actions["Open Sovereign Grid"] == "/console/sovereign-grid"
    assert "/products" not in actions.values()
    assert "/self-host" not in actions.values()
