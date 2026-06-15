from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WOW_TEXT = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "components" / "wow").glob("*.py"))
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def test_wow_preview_and_unavailable_states_are_visible() -> None:
    for phrase in ("Preview only", "Backend remains the source of truth", "Insufficient evidence", "No evidence chain available yet", "unknown", "unavailable"):
        assert phrase in WOW_TEXT


def test_command_center_route_registered() -> None:
    assert 'route="/console/command-center"' in APP
