from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")
CONSOLE_TEXT = "\n".join(
    path.read_text(encoding="utf-8")
    for path in [
        ROOT / "routes" / "console.py",
        ROOT / "routes" / "console_trace.py",
        ROOT / "routes" / "console_evidence.py",
        ROOT / "routes" / "console_provider_health.py",
        ROOT / "components" / "console" / "dashboard_shell.py",
    ]
).lower()


def test_console_routes_exist() -> None:
    for route in ("/console", "/console/trace", "/console/evidence", "/console/provider-health", "/console/market-intelligence", "/console/time-machine", "/console/sovereign-grid", "/console/policy", "/console/audit", "/console/deployment", "/console/api-explorer"):
        assert f'route="{route}"' in APP


def test_console_pages_are_display_only_and_no_custody_safe() -> None:
    assert "no execution controls" in CONSOLE_TEXT
    assert "custody controls" in CONSOLE_TEXT
    assert "signing controls" in CONSOLE_TEXT
    forbidden_controls = ("sign transaction", "send bitcoin", "sweep wallet", "broadcast transaction")
    for phrase in forbidden_controls:
        assert phrase not in CONSOLE_TEXT
