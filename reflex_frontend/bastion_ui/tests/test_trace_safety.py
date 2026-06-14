from pathlib import Path

from bastion_ui.security.safety_copy import FORBIDDEN_WORDING, REQUIRED_SAFETY_COPY

ROOT = Path(__file__).resolve().parents[1]
TRACE_SOURCES = [
    ROOT / "routes" / "check.py",
    ROOT / "routes" / "trace.py",
    ROOT / "routes" / "trace_report.py",
    ROOT / "routes" / "proof_packet.py",
    ROOT / "routes" / "console_trace.py",
    ROOT / "components" / "ui" / "safety_banner.py",
]


def test_required_safety_copy_is_visible_on_trace_surfaces() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in TRACE_SOURCES)
    for phrase in REQUIRED_SAFETY_COPY:
        assert phrase in combined or phrase in " ".join(REQUIRED_SAFETY_COPY)


def test_forbidden_wording_is_absent_from_trace_surfaces() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in TRACE_SOURCES)
    for phrase in FORBIDDEN_WORDING:
        assert phrase not in combined
