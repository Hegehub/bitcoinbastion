from __future__ import annotations

from pathlib import Path

from bastion_ui.security.market_safety_copy import (
    MARKET_TIME_MACHINE_NO_CUSTODY_COPY,
    MARKET_TIME_MACHINE_SAFETY_COPY,
)

ROOT = Path(__file__).resolve().parents[3]
MARKET_PATHS = (
    ROOT / "reflex_frontend/bastion_ui/components/market",
    ROOT / "reflex_frontend/bastion_ui/routes/market_time_machine.py",
    ROOT / "reflex_frontend/bastion_ui/routes/market_timeline.py",
    ROOT / "reflex_frontend/bastion_ui/routes/market_signals.py",
    ROOT / "reflex_frontend/bastion_ui/routes/market_evidence.py",
    ROOT / "reflex_frontend/bastion_ui/routes/market_narratives.py",
    ROOT / "reflex_frontend/bastion_ui/routes/market_sources.py",
    ROOT / "reflex_frontend/bastion_ui/security/market_safety_copy.py",
)
FORBIDDEN_PARTS = (
    ("guaranteed", "profit"),
    ("guaranteed", "signal"),
    ("certain", "prediction"),
    ("risk-free", "trade"),
    ("buy", "now"),
    ("sell", "now"),
    ("approved", "trade"),
    ("perfect", "entry"),
)


def _market_files() -> list[Path]:
    files: list[Path] = []
    for path in MARKET_PATHS:
        if path.is_dir():
            files.extend(path.rglob("*.py"))
        else:
            files.append(path)
    return files


def test_market_time_machine_safety_copy_present() -> None:
    assert "not " + "financial advice" in MARKET_TIME_MACHINE_SAFETY_COPY
    assert "not a trading instruction" in MARKET_TIME_MACHINE_SAFETY_COPY
    assert "not a guarantee of future price movement" in MARKET_TIME_MACHINE_SAFETY_COPY
    assert "advisory-only" in MARKET_TIME_MACHINE_SAFETY_COPY
    assert "Signals require operator review" in MARKET_TIME_MACHINE_SAFETY_COPY
    assert "stale data reduce confidence" in MARKET_TIME_MACHINE_SAFETY_COPY


def test_market_time_machine_no_custody_copy_present() -> None:
    assert "seed phrases" in MARKET_TIME_MACHINE_NO_CUSTODY_COPY
    assert "private keys" in MARKET_TIME_MACHINE_NO_CUSTODY_COPY
    assert "wallet files" in MARKET_TIME_MACHINE_NO_CUSTODY_COPY
    assert "exchange API secrets" in MARKET_TIME_MACHINE_NO_CUSTODY_COPY
    assert "signing material" in MARKET_TIME_MACHINE_NO_CUSTODY_COPY
    assert "does not execute trades" in MARKET_TIME_MACHINE_NO_CUSTODY_COPY


def test_forbidden_market_wording_absent_from_rendered_market_modules() -> None:
    text = "\n".join(path.read_text(encoding="utf-8") for path in _market_files()).lower()
    for left, right in FORBIDDEN_PARTS:
        assert f"{left} {right}" not in text


def test_forbidden_market_wording_test_list_covers_required_phrases() -> None:
    phrases = {f"{left} {right}" for left, right in FORBIDDEN_PARTS}
    assert "guaranteed profit" in phrases
    assert "guaranteed signal" in phrases
    assert "certain prediction" in phrases
    assert "risk-free trade" in phrases
    assert "buy now" in phrases
    assert "sell now" in phrases
    assert "approved trade" in phrases
    assert "perfect entry" in phrases
