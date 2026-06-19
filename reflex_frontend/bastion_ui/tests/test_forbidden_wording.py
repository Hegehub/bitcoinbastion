from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PARTS = [
    ("clean", "address"),
    ("dirty", "address"),
    ("criminal", "address"),
    ("guaranteed", "safe"),
    ("approved", "payment"),
    ("verified", "illicit"),
]
EXCLUDED_FILES = {Path(__file__).name}


def test_forbidden_wording_absent_from_user_facing_modules() -> None:
    offenders: list[str] = []
    for path in ROOT.rglob("*.py"):
        if path.name in EXCLUDED_FILES or "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for left, right in FORBIDDEN_PARTS:
            phrase = f"{left} {right}"
            if phrase in text:
                offenders.append(f"{path.relative_to(ROOT)}:{phrase}")
    assert offenders == []
