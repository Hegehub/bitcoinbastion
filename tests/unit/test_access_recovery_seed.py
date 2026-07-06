from app.services.access.recovery_seed import (
    RecoveryPhraseStrength,
    generate_recovery_phrase,
    recovery_phrase_commitment,
    reject_bitcoin_wallet_seed_warning,
    validate_recovery_phrase_format,
)


def test_generate_12_word_bastion_recovery_seed() -> None:
    result = generate_recovery_phrase(RecoveryPhraseStrength.WORDS_12)
    assert result.word_count == 12
    assert len(result.words) == 12
    assert result.purpose == "bastion_access_recovery"
    assert result.display_once is True
    assert "NOT your Bitcoin wallet seed" in result.warning


def test_generate_24_word_bastion_recovery_seed() -> None:
    result = generate_recovery_phrase(RecoveryPhraseStrength.WORDS_24)
    assert result.word_count == 24
    assert len(result.words) == 24


def test_commitment_stable_and_pepper_bound() -> None:
    phrase = " ".join(generate_recovery_phrase(RecoveryPhraseStrength.WORDS_12).words)
    assert recovery_phrase_commitment(phrase, "pepper") == recovery_phrase_commitment(phrase, "pepper")
    assert recovery_phrase_commitment(phrase, "pepper") != recovery_phrase_commitment(phrase, "other")


def test_validate_recovery_phrase_word_count() -> None:
    phrase = " ".join(generate_recovery_phrase(RecoveryPhraseStrength.WORDS_12).words)
    assert validate_recovery_phrase_format(phrase, RecoveryPhraseStrength.WORDS_12).valid is True
    assert validate_recovery_phrase_format(phrase, RecoveryPhraseStrength.WORDS_24).valid is False


def test_bitcoin_seed_and_private_key_inputs_rejected() -> None:
    bitcoin_seed = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    for value in (bitcoin_seed, "xprv9s21ZrQH143K3exampleprivatekeymaterialbitcoinwallet"):
        try:
            reject_bitcoin_wallet_seed_warning(value)
        except ValueError as exc:
            assert "bitcoin" in str(exc)
        else:  # pragma: no cover
            raise AssertionError("bitcoin wallet material accepted")
