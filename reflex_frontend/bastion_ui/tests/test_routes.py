from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.py").read_text(encoding="utf-8")


def test_trace_and_console_routes_are_registered() -> None:
    for route in (
        "/check",
        "/trace",
        "/trace/[report_id]",
        "/trace/[report_id]/proof-packet",
        "/console",
        "/console/trace",
        "/console/evidence",
        "/console/provider-health",
    ):
        assert f'route="{route}"' in APP
