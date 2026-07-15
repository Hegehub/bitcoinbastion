from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONSOLE_COMPONENTS = ROOT / "frontend/bastion_ui/components/console"
CONSOLE_ROUTES = ROOT / "frontend/bastion_ui/routes"
FORBIDDEN_PARTS = (
    ("clean", "address"),
    ("dirty", "address"),
    ("criminal", "address"),
    ("guaranteed", "safe"),
    ("approved", "payment"),
    ("verified", "illicit"),
)
SENSITIVE_TERMS = (
    "seed phrase",
    "mnemonic",
    "private key",
    "xprv",
    "yprv",
    "zprv",
    "wallet.dat",
    "keystore",
    "signing material",
)


def _advanced_text() -> str:
    files = [
        CONSOLE_COMPONENTS / "market_intelligence_panel.py",
        CONSOLE_COMPONENTS / "time_machine_panel.py",
        CONSOLE_COMPONENTS / "sovereign_grid_panel.py",
        CONSOLE_COMPONENTS / "api_explorer_panel.py",
        CONSOLE_ROUTES / "console_market_intelligence.py",
        CONSOLE_ROUTES / "console_time_machine.py",
        CONSOLE_ROUTES / "console_sovereign_grid.py",
        CONSOLE_ROUTES / "console_api_explorer.py",
    ]
    return "\n".join(path.read_text(encoding="utf-8") for path in files).lower()


def test_forbidden_wording_absent_from_advanced_console_ui() -> None:
    text = _advanced_text()
    for left, right in FORBIDDEN_PARTS:
        assert f"{left} {right}" not in text


def test_sensitive_material_terms_only_appear_in_warning_copy() -> None:
    text = _advanced_text()
    for term in SENSITIVE_TERMS:
        if term in text:
            assert "never submit" in text or "does not request" in text
    assert "rx.input" not in text
    assert "type=\"file\"" not in text
