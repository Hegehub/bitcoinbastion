from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFLEX_ROOT = ROOT.parents[0]
FORBIDDEN_PARTS = [
    ("clean", "address"),
    ("dirty", "address"),
    ("criminal", "address"),
    ("guaranteed", "safe"),
    ("approved", "payment"),
    ("verified", "illicit"),
]
ALLOWED_TEST_FILES = {
    Path(__file__).resolve(),
    REFLEX_ROOT / "tests" / "test_forbidden_wording.py",
    REFLEX_ROOT / "tests" / "test_wow_forbidden_wording.py",
    REFLEX_ROOT / "tests" / "test_console_safety.py",
}
SCAN_ROOTS = (
    ROOT / "routes",
    ROOT / "components",
    ROOT / "security",
    ROOT / "state",
    ROOT / "services",
    ROOT / "tests",
    REFLEX_ROOT / "docs",
)


def _scan_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        files.extend(path for path in root.rglob("*") if path.suffix in {".py", ".md"})
    return files


def test_forbidden_wording_absent_from_reflex_user_facing_source_docs_and_fixtures() -> None:
    offenders: list[str] = []
    for path in _scan_files():
        if path.resolve() in ALLOWED_TEST_FILES or "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for left, right in FORBIDDEN_PARTS:
            phrase = f"{left} {right}"
            if phrase in text:
                offenders.append(f"{path.relative_to(REFLEX_ROOT)}:{phrase}")
    assert offenders == []


def test_allowed_alternatives_are_available_in_safety_copy() -> None:
    text = (ROOT / "security" / "safety_copy.py").read_text(encoding="utf-8").lower()
    assert "advisory-only" in text
    assert "manual review recommended" in text
    assert "provider disagreement" in text
    assert "low confidence" in text
    assert "not legal verification" in text
    assert "not bitcoin consensus proof" in text
    assert "no custody" in text
    assert "public bitcoin addresses only" in text
