from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def test_public_routes_are_registered() -> None:
    for route in (
        "/",
        "/platform",
        "/developers",
        "/operations",
        "/manifesto",
        "/evidence",
        "/status",
        "/roadmap",
        "/security",
        "/docs",
    ):
        assert f'route="{route}"' in APP


def test_trace_and_console_routes_are_registered_after_prompt_26() -> None:
    assert 'route="/trace"' in APP
    assert 'route="/console"' in APP
