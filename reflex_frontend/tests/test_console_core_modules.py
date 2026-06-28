from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "reflex_frontend/bastion_ui/app.py"
CONSOLE_COMPONENTS = ROOT / "reflex_frontend/bastion_ui/components/console"

ROUTES = (
    "/console/trace",
    "/console/evidence",
    "/console/provider-health",
    "/console/policy",
    "/console/audit",
)


def test_console_core_routes_exist() -> None:
    text = APP.read_text(encoding="utf-8")
    for route in ROUTES:
        assert f'route="{route}"' in text


def test_console_modules_use_dashboard_shell() -> None:
    for name in (
        "console_trace.py",
        "console_evidence.py",
        "console_provider_health.py",
        "console_policy.py",
        "console_audit.py",
    ):
        text = (ROOT / f"reflex_frontend/bastion_ui/routes/{name}").read_text(encoding="utf-8")
        assert "dashboard_shell" in text


def test_console_module_panels_include_baseline_states() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8") for path in CONSOLE_COMPONENTS.glob("*_panel.py")
    )
    assert "Recent Trace reports panel" in text
    assert "Evidence Console baseline view" in text
    assert "Unknown provider state is never displayed as healthy" in text
    assert "Policy Console is read-only" in text
    assert "Immutable audit storage is not claimed" in text
