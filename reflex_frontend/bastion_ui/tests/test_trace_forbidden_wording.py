from __future__ import annotations

from pathlib import Path

BLOCKED_PHRASES = (
    "clean" + " address",
    "dirty" + " address",
    "criminal" + " address",
    "guaranteed" + " safe",
    "approved" + " payment",
    "verified" + " illicit",
)


def test_trace_public_files_avoid_forbidden_wording() -> None:
    root = Path(__file__).resolve().parents[1]
    files = [
        *list((root / "routes").glob("trace.py")),
        *list((root / "routes").glob("check.py")),
        *list((root / "components" / "trace").glob("*.py")),
    ]
    for path in files:
        text = path.read_text().casefold()
        for phrase in BLOCKED_PHRASES:
            assert phrase not in text
