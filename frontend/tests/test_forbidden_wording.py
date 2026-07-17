from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PARTS = (
    ("clean", "address"),
    ("dirty", "address"),
    ("criminal", "address"),
    ("guaranteed", "safe"),
    ("approved", "payment"),
    ("verified", "illicit"),
)
ALLOWED_FIXTURES = {
    "tests/test_forbidden_wording.py",
    "tests/test_console_safety.py",
    "tests/test_wow_forbidden_wording.py",
}


def test_forbidden_phrases_absent_from_reflex_source_docs_and_tests() -> None:
    offenders: list[str] = []
    for path in ROOT.rglob("*"):
        if path.is_dir() or "__pycache__" in path.parts or path.suffix not in {".py", ".md"}:
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in ALLOWED_FIXTURES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for left, right in FORBIDDEN_PARTS:
            phrase = f"{left} {right}"
            if phrase in text:
                offenders.append(f"{rel}:{phrase}")
    assert offenders == []
