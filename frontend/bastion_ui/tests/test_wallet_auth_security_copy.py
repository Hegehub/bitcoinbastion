from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_mandatory_wallet_security_copy_and_no_password_form() -> None:
    text = (ROOT / "components/auth/access.py").read_text()
    assert "Bastion will never ask for your Bitcoin seed" in text
    assert "This signature does not authorize a Bitcoin transaction" in text
    assert "Use a dedicated Bastion authentication wallet or address" in text
    assert 'type="password"' not in text
    assert "seed_input" not in text


def test_browser_is_not_root_of_trust() -> None:
    assert "Browser is not a root of trust" in (ROOT / "components/auth/access.py").read_text()
