from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ROOTS = (
    ROOT / "reflex_frontend/bastion_ui/components/market",
    ROOT / "reflex_frontend/bastion_ui/routes/console_market_intelligence.py",
    ROOT / "reflex_frontend/bastion_ui/security/market_safety.py",
)
FORBIDDEN_PARTS = (
    ("guaranteed", "profit"),
    ("guaranteed", "signal"),
    ("buy", "now"),
    ("sell", "now"),
    ("safe", "trade"),
    ("risk", "free"),
    ("approved", "trade"),
    ("certain", "outcome"),
)


def _files() -> list[Path]:
    files: list[Path] = []
    for root in ROOTS:
        if root.is_dir():
            files.extend(root.rglob("*.py"))
        else:
            files.append(root)
    return files


def test_forbidden_trading_claims_absent_from_market_ui() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in _files()).lower()
    for left, right in FORBIDDEN_PARTS:
        assert f"{left} {right}" not in text


def test_phrase_list_covers_required_forbidden_claims() -> None:
    phrases = {f"{left} {right}" for left, right in FORBIDDEN_PARTS}
    assert "guaranteed profit" in phrases
    assert "guaranteed signal" in phrases
    assert "buy now" in phrases
    assert "sell now" in phrases
    assert "safe trade" in phrases
    assert "risk free" in phrases
    assert "approved trade" in phrases
    assert "certain outcome" in phrases
