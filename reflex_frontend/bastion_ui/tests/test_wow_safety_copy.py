from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WOW_TEXT = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "components" / "wow").glob("*.py"))


def test_wow_required_safety_copy_present() -> None:
    required = (
        "Advisory-only.",
        "Not legal verification.",
        "Not Bitcoin consensus proof.",
        "No custody.",
        "Public Bitcoin addresses only.",
        "Never enter seed phrases, private keys, wallet files or signing material.",
        "Historical similarity does not guarantee future market behavior.",
        "Correlation is not proof of causation.",
        "Operator review required for risky actions.",
    )
    for phrase in required:
        assert phrase in WOW_TEXT


def test_specific_wow_limitations_present() -> None:
    assert "Not financial advice." in WOW_TEXT
    assert "Simulation only." in WOW_TEXT
    assert "Final action button is disabled by default." in WOW_TEXT
