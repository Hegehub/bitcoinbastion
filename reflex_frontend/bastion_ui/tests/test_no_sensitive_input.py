from bastion_ui.security.address_validation import validate_public_bitcoin_address
from bastion_ui.security.forbidden_inputs import FORBIDDEN_PATTERNS


def test_rejects_forbidden_sensitive_inputs() -> None:
    for pattern in FORBIDDEN_PATTERNS:
        valid, message = validate_public_bitcoin_address(pattern)
        assert not valid
        assert message == "Never enter seed phrases, private keys, wallet files or signing material."


def test_rejects_empty_input() -> None:
    valid, message = validate_public_bitcoin_address("")
    assert not valid
    assert message == "Address is required."


def test_accepts_public_bitcoin_address_examples() -> None:
    for address in (
        "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080",
        "1BoatSLRHtKNngkdXEeobR76b53LETtpyT",
        "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy",
    ):
        valid, message = validate_public_bitcoin_address(address)
        assert valid
        assert message is None
