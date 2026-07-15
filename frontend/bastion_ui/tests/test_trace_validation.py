from __future__ import annotations

from bastion_ui.security.address_validation import validate_public_bitcoin_address
from bastion_ui.security.forbidden_inputs import looks_like_sensitive_wallet_material

BC1 = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080"
LEGACY = "1BoatSLRHtKNngkdXEeobR76b53LETtpyT"
NESTED = "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy"
TWELVE = "alpha bravo cactus delta eagle forest galaxy harbor island jungle kitten lemon"
TWENTY_FOUR = (
    f"{TWELVE} mango nectar orange planet quantum river silver tiger uncle velvet winter xenon"
)
WIF = "5HueCGU8rMjxEXxiPuD5BDuRaT2wH6GZK8LrqsqYyW5f3pQn4xA"


def test_accepts_plausible_public_bitcoin_addresses() -> None:
    for address in (BC1, LEGACY, NESTED):
        result = validate_public_bitcoin_address(address)
        assert result.ok
        assert result.normalized_address == address


def test_rejects_empty_and_obvious_invalid_input() -> None:
    assert not validate_public_bitcoin_address("").ok
    assert not validate_public_bitcoin_address("hello bitcoin").ok


def test_rejects_sensitive_wallet_material() -> None:
    rejected = [
        "seed phrase",
        "mnemonic phrase",
        "private key",
        "xprv9s21ZrQH143Kexample",
        "yprv9s21ZrQH143Kexample",
        "zprv9s21ZrQH143Kexample",
        "tprv9s21ZrQH143Kexample",
        "wallet.dat",
        "keystore",
        "signing material",
        TWELVE,
        TWENTY_FOUR,
        WIF,
        '{"private": "key"}',
    ]
    for value in rejected:
        assert looks_like_sensitive_wallet_material(value)
        assert not validate_public_bitcoin_address(value).ok


def test_rejected_sensitive_input_is_not_sent_to_api_client() -> None:
    calls: list[str] = []
    candidate = validate_public_bitcoin_address(WIF)
    if candidate.ok:
        calls.append(candidate.normalized_address)
    assert calls == []
