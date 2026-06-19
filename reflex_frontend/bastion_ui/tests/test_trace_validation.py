from __future__ import annotations

from bastion_ui.security.address_validation import validate_public_bitcoin_address
from bastion_ui.security.forbidden_inputs import looks_like_sensitive_wallet_material

VALID_BC1 = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080"
VALID_LEGACY = "1BoatSLRHtKNngkdXEeobR76b53LETtpyT"
VALID_NESTED = "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy"
WIF = "KwdMAjQjYV6N4D4eJvH2v8mLvx6AV3M5iYzX4N4h7P6xQxP4WvMe"
TWELVE_WORDS = "alpha bravo cactus delta ember forest galaxy harbor island jungle kernel lemon"
TWENTY_FOUR_WORDS = (
    "alpha bravo cactus delta ember forest galaxy harbor island jungle kernel lemon "
    "marble nectar orbit pencil quantum river silver tunnel uncle velvet winter yellow"
)


def test_trace_input_accepts_plausible_public_addresses() -> None:
    assert validate_public_bitcoin_address(VALID_BC1).ok
    assert validate_public_bitcoin_address(VALID_LEGACY).ok
    assert validate_public_bitcoin_address(VALID_NESTED).ok


def test_trace_input_rejects_empty_and_invalid_text() -> None:
    assert not validate_public_bitcoin_address("").ok
    assert not validate_public_bitcoin_address("hello bitcoin").ok


def test_trace_input_rejects_sensitive_material() -> None:
    for value in [
        "seed phrase: never log",
        TWELVE_WORDS,
        TWENTY_FOUR_WORDS,
        "xprv123456789ABCDEFGH",
        "yprv123456789ABCDEFGH",
        "zprv123456789ABCDEFGH",
        "tprv123456789ABCDEFGH",
        WIF,
        "wallet.dat",
        "keystore payload",
        '{"private_key": "secret"}',
        "raw signing material",
    ]:
        assert looks_like_sensitive_wallet_material(value)
        assert not validate_public_bitcoin_address(value).ok
