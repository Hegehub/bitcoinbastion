from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

TRACE_PATHS = (
    ROOT / "reflex_frontend/bastion_ui/routes/check.py",
    ROOT / "reflex_frontend/bastion_ui/routes/trace.py",
    ROOT / "reflex_frontend/bastion_ui/components/trace",
)
FORBIDDEN_PARTS = (
    ("clean", "address"),
    ("dirty", "address"),
    ("criminal", "address"),
    ("guaranteed", "safe"),
    ("approved", "payment"),
    ("verified", "illicit"),
)


def test_forbidden_wording_absent_from_trace_public_flow() -> None:
    files: list[Path] = []
    for path in TRACE_PATHS:
        if path.is_dir():
            files.extend(path.rglob("*.py"))
        else:
            files.append(path)
    text = "\n".join(path.read_text(encoding="utf-8") for path in files).lower()
    for left, right in FORBIDDEN_PARTS:
        assert f"{left} {right}" not in text
