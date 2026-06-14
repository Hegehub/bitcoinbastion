from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "components" / "console").glob("*.py"))


def test_console_components_show_degraded_and_readonly_copy() -> None:
    for phrase in ("Read-only", "Advisory", "No custody", "Operator review", "Evidence-based", "Degraded visible"):
        assert phrase in TEXT
    assert "degraded" in TEXT.lower()
    assert "fallback" in TEXT.lower()
    assert "stale" in TEXT.lower()
    assert "unavailable" in TEXT.lower()
