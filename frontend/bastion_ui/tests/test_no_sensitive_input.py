from __future__ import annotations

from pathlib import Path

from bastion_ui.security.address_validation import validate_public_bitcoin_address
from bastion_ui.security.forbidden_inputs import (
    SENSITIVE_WALLET_INPUT_MESSAGE,
    looks_like_sensitive_wallet_material,
)

ROOT = Path(__file__).resolve().parents[1]
SENSITIVE_PROMPTS = (
    "enter your seed",
    "please enter seed",
    "enter your private key",
    "upload wallet.dat",
    "upload keystore",
    "paste xprv",
    "paste yprv",
    "paste zprv",
    "signing material input",
)
VALID_ADDRESS = "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080"
SENSITIVE_VALUES = (
    "seed phrase",
    "mnemonic phrase",
    "private key",
    "abandon ability able about above absent absorb abstract absurd abuse access accident",
    (
        "abandon ability able about above absent absorb abstract absurd abuse access accident "
        "account accuse achieve acid acoustic acquire across act action actor actress actual"
    ),
    "xprv9s21ZrQH143K3example",
    "yprvAJK3example",
    "zprvAWgYBBk7JR8Gjexample",
    "wallet.dat",
    '{"keystore": {"private": "material"}}',
    "KwdMAj2BGe2M4A4V2xY7dUQmP5xwVvFghm7N6fYB3GdQ2g8U9zQ1",
    "signing material",
)


def test_valid_public_bitcoin_address_is_not_blocked_by_sensitive_detector() -> None:
    assert not looks_like_sensitive_wallet_material(VALID_ADDRESS)
    result = validate_public_bitcoin_address(VALID_ADDRESS)
    assert result.ok is True
    assert result.normalized_address == VALID_ADDRESS


def test_sensitive_material_patterns_are_rejected() -> None:
    for value in SENSITIVE_VALUES:
        assert looks_like_sensitive_wallet_material(value), value
        result = validate_public_bitcoin_address(value)
        assert result.ok is False
        assert result.error == SENSITIVE_WALLET_INPUT_MESSAGE
        if value.startswith(("xprv", "yprv", "zprv", "K")) or "{" in value:
            assert value not in result.error


def test_validation_error_is_user_safe_and_does_not_echo_rejected_value() -> None:
    rejected = "xprv9s21ZrQH143K3secret"
    result = validate_public_bitcoin_address(rejected)
    assert result.ok is False
    assert "public Bitcoin addresses" in result.error
    assert "Never enter seed phrases" in result.error
    assert rejected not in result.error


def test_evidence_and_proof_packet_ui_do_not_request_sensitive_material() -> None:
    files = list((ROOT / "components/evidence").glob("*.py")) + [ROOT / "routes" / "evidence.py"]
    for path in files:
        text = path.read_text(encoding="utf-8").lower()
        for prompt in SENSITIVE_PROMPTS:
            assert prompt not in text, f"{prompt!r} found in {path}"


def test_no_new_evidence_input_fields_are_added() -> None:
    evidence_component_text = "\n".join(
        path.read_text(encoding="utf-8") for path in (ROOT / "components/evidence").glob("*.py")
    )
    assert "rx.input" not in evidence_component_text
