import logging

from app.services.access.recovery_seed import RecoveryPhraseStrength, generate_recovery_phrase, recovery_phrase_commitment


def test_raw_recovery_phrase_not_logged(caplog) -> None:
    phrase = " ".join(generate_recovery_phrase(RecoveryPhraseStrength.WORDS_12).words)
    with caplog.at_level(logging.INFO):
        commitment = recovery_phrase_commitment(phrase, "pepper")
        logging.getLogger("access.recovery.test").info("stored recovery commitment %s", commitment)
    assert phrase not in caplog.text
    assert "bastion_recovery_phrase" not in caplog.text
