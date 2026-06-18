from __future__ import annotations

from pathlib import Path

BLOCKED_WORDING = (
    "clean" + " address",
    "dirty" + " address",
    "criminal" + " address",
    "guaranteed" + " safe",
    "approved" + " payment",
    "verified" + " illicit",
)

SCAN_ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {"tests", "__pycache__"}


def test_forbidden_wording_absent_from_user_facing_modules() -> None:
    offenders: list[str] = []
    for path in SCAN_ROOT.rglob("*.py"):
        if EXCLUDED_PARTS.intersection(path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").casefold()
        for phrase in BLOCKED_WORDING:
            if phrase in text:
                offenders.append(f"{path.relative_to(SCAN_ROOT)}:{phrase}")
    assert offenders == []
