from pathlib import Path


def test_recovery_is_capsule_not_password_reset_and_has_no_wallet_secret_inputs() -> None:
    root = Path(__file__).resolve().parents[1]
    text = (
        root.joinpath("components/auth/access.py").read_text()
        + root.joinpath("routes/wallet_auth.py").read_text()
    )
    assert "Recovery Capsule" in text
    assert "Never enter your Bitcoin seed or private key" in text
    lowered = text.lower()
    for forbidden_label in (
        'label="seed"',
        'label="seed phrase"',
        'label="mnemonic"',
        'label="private key"',
        'label="xprv"',
    ):
        assert forbidden_label not in lowered
    assert "reset password" not in lowered
