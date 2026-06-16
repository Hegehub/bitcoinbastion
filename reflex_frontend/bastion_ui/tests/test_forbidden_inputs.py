from __future__ import annotations

from bastion_ui.security.forbidden_inputs import looks_like_sensitive_wallet_material


def test_forbidden_wallet_material_is_detected() -> None:
    assert looks_like_sensitive_wallet_material("seed phrase")
    assert looks_like_sensitive_wallet_material("mnemonic backup")
    assert looks_like_sensitive_wallet_material("private key")
    assert looks_like_sensitive_wallet_material("xprv9s21ZrQH143K3")
    assert looks_like_sensitive_wallet_material("yprv example")
    assert looks_like_sensitive_wallet_material("zprv example")
    assert looks_like_sensitive_wallet_material("wallet.dat")
    assert looks_like_sensitive_wallet_material("keystore json")
    assert looks_like_sensitive_wallet_material("signing material")


def test_mnemonic_length_phrases_are_detected() -> None:
    twelve_words = (
        "abandon ability able about above absent absorb abstract absurd abuse access accident"
    )
    twenty_four_words = f"{twelve_words} {twelve_words}"

    assert looks_like_sensitive_wallet_material(twelve_words)
    assert looks_like_sensitive_wallet_material(twenty_four_words)


def test_public_bitcoin_address_like_text_is_not_sensitive_wallet_material() -> None:
    assert not looks_like_sensitive_wallet_material("bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080")
