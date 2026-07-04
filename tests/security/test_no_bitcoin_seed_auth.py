from app.services.access.recovery_seed import recovery_phrase_commitment, reject_bitcoin_wallet_seed_warning


def test_bitcoin_wallet_seed_not_accepted_for_access_recovery() -> None:
    phrase = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    try:
        recovery_phrase_commitment(phrase, "pepper")
    except ValueError as exc:
        assert str(exc) == "bitcoin_seed_input_rejected"
    else:  # pragma: no cover
        raise AssertionError("Bitcoin wallet seed accepted")


def test_bitcoin_private_key_not_accepted_for_access_recovery() -> None:
    try:
        reject_bitcoin_wallet_seed_warning("xprv9s21ZrQH143K3exampleprivatekeymaterialbitcoinwallet")
    except ValueError as exc:
        assert "bitcoin" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Bitcoin private key accepted")
