from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_reflex_core_config_and_routes() -> None:
    rxconfig = (ROOT / "frontend/rxconfig.py").read_text(encoding="utf-8")
    app = (ROOT / "frontend/bastion_ui/app.py").read_text(encoding="utf-8")
    assert "frontend_port=3001" in rxconfig.replace(" ", "")
    assert "backend_port=8001" in rxconfig.replace(" ", "")
    for route in [
        "/check",
        "/trace",
        "/trace/[report_id]",
        "/trace/[report_id]/proof-packet",
        "/console",
        "/console/trace",
        "/console/evidence",
        "/console/market-intelligence",
        "/console/time-machine",
        "/console/sovereign-grid",
        "/console/policy",
        "/console/audit",
        "/console/command-center",
    ]:
        assert f'route="{route}"' in app


def test_reflex_navigation_uses_current_public_paths() -> None:
    nav = (ROOT / "frontend/bastion_ui/components/layout/command_palette.py").read_text(
        encoding="utf-8"
    )
    assert "/platform" in nav
    assert "/operations" in nav
    assert "/products" not in nav
    assert "/self-host" not in nav
