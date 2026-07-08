"""Bastion Access Recovery Phrase generation and commitment helpers.

This module intentionally never derives Bitcoin keys, never calls wallet seed
APIs, and never stores raw recovery phrases. User-facing text must call this a
Bastion Recovery Seed or Access Recovery Phrase, not a Bitcoin wallet seed.
"""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from enum import StrEnum

from app.services.access.crypto.hashing import hmac_sha256_prefixed

RECOVERY_SAFETY_WARNING = (
    "This is NOT your Bitcoin wallet seed. Never enter your Bitcoin wallet seed "
    "into Bastion. Bastion will never ask for your Bitcoin seed or private keys. "
    "This phrase restores access rights only, not Bitcoin funds."
)

# Dedicated Bastion word list. It is intentionally not a Bitcoin key derivation
# word list and is used only as human-readable entropy labels.
_BASTION_WORDS = tuple(
    f"bastion{index:04d}" for index in range(2048)
)
_COMMON_BITCOIN_SEED_WORDS = {
    "abandon",
    "ability",
    "able",
    "about",
    "above",
    "absent",
    "absorb",
    "abstract",
    "absurd",
    "abuse",
    "access",
    "accident",
    "account",
    "accuse",
    "achieve",
    "acid",
    "acoustic",
    "acquire",
    "across",
    "act",
    "action",
    "actor",
    "actress",
    "actual",
    "adapt",
    "add",
    "addict",
    "address",
    "adjust",
    "admit",
    "adult",
    "advance",
    "advice",
    "aerobic",
    "affair",
    "afford",
    "afraid",
    "again",
    "age",
    "agent",
    "agree",
    "ahead",
    "aim",
    "air",
    "airport",
    "aisle",
    "alarm",
    "album",
    "alcohol",
    "alert",
    "alien",
    "all",
    "alley",
    "allow",
    "almost",
    "alone",
    "alpha",
    "already",
    "also",
    "alter",
    "always",
    "amateur",
    "amazing",
    "among",
    "amount",
    "amused",
    "analyst",
    "anchor",
    "ancient",
    "anger",
    "angle",
    "angry",
    "animal",
    "ankle",
    "announce",
    "annual",
    "another",
    "answer",
    "antenna",
    "antique",
    "anxiety",
    "any",
    "apart",
    "apology",
    "appear",
    "apple",
    "approve",
    "april",
    "arch",
    "arctic",
    "area",
    "arena",
    "argue",
    "arm",
    "armed",
    "armor",
    "army",
    "around",
    "arrange",
    "arrest",
    "arrive",
    "arrow",
    "art",
    "artefact",
    "artist",
    "artwork",
    "ask",
    "aspect",
    "assault",
    "asset",
    "assist",
    "assume",
    "asthma",
    "athlete",
    "atom",
    "attack",
    "attend",
    "attitude",
    "attract",
    "auction",
    "audit",
    "august",
    "aunt",
    "author",
    "auto",
    "autumn",
    "average",
    "avocado",
    "avoid",
    "awake",
    "aware",
    "away",
    "awesome",
    "awful",
    "awkward",
    "axis",
    "baby",
    "bachelor",
    "bacon",
    "badge",
    "bag",
    "balance",
    "balcony",
    "ball",
    "bamboo",
    "banana",
    "banner",
    "bar",
    "barely",
    "bargain",
    "barrel",
    "base",
    "basic",
    "basket",
    "battle",
    "beach",
    "bean",
    "beauty",
    "because",
    "become",
    "beef",
    "before",
    "begin",
    "behave",
    "behind",
    "believe",
    "below",
    "belt",
    "bench",
    "benefit",
    "best",
    "betray",
    "better",
    "between",
    "beyond",
    "bicycle",
    "bid",
    "bike",
    "bind",
    "biology",
    "bird",
    "birth",
    "bitter",
    "black",
    "blade",
    "blame",
    "blanket",
    "blast",
    "bleak",
    "bless",
    "blind",
    "blood",
    "blossom",
    "blouse",
    "blue",
    "blur",
    "blush",
    "board",
    "boat",
}
_BITCOIN_PRIVATE_KEY_PATTERNS = (
    re.compile(r"\bxprv[1-9A-HJ-NP-Za-km-z]{20,}\b"),
    re.compile(r"\b[KL5][1-9A-HJ-NP-Za-km-z]{50,}\b"),
)


class RecoveryPhraseStrength(StrEnum):
    WORDS_12 = "words_12"
    WORDS_24 = "words_24"


class RecoveryPhrasePurpose(StrEnum):
    BASTION_ACCESS_RECOVERY = "bastion_access_recovery"


@dataclass(frozen=True)
class RecoveryPhraseResult:
    words: list[str]
    word_count: int
    purpose: str
    warning: str
    display_once: bool = True

    @property
    def phrase(self) -> str:
        return " ".join(self.words)


@dataclass(frozen=True)
class RecoveryPhraseValidationResult:
    valid: bool
    word_count: int
    purpose: str
    reason: str | None = None
    warning: str = RECOVERY_SAFETY_WARNING


def generate_recovery_phrase(strength: RecoveryPhraseStrength) -> RecoveryPhraseResult:
    word_count = _word_count(strength)
    words = [secrets.choice(_BASTION_WORDS) for _ in range(word_count)]
    return RecoveryPhraseResult(
        words=words,
        word_count=word_count,
        purpose=RecoveryPhrasePurpose.BASTION_ACCESS_RECOVERY.value,
        warning=RECOVERY_SAFETY_WARNING,
    )


def recovery_phrase_commitment(phrase: str, server_pepper: str) -> str:
    reject_bitcoin_wallet_seed_warning(phrase)
    normalized = _normalize_phrase(phrase)
    if not normalized:
        raise ValueError("bastion_recovery_phrase_required")
    return hmac_sha256_prefixed(server_pepper, f"bastion_access_recovery:v1:{normalized}")


def validate_recovery_phrase_format(
    phrase: str, expected_strength: RecoveryPhraseStrength
) -> RecoveryPhraseValidationResult:
    try:
        reject_bitcoin_wallet_seed_warning(phrase)
    except ValueError as exc:
        return RecoveryPhraseValidationResult(
            valid=False,
            word_count=len(_split_words(phrase)),
            purpose=RecoveryPhrasePurpose.BASTION_ACCESS_RECOVERY.value,
            reason=str(exc),
        )
    words = _split_words(phrase)
    expected_count = _word_count(expected_strength)
    if len(words) != expected_count:
        return RecoveryPhraseValidationResult(
            valid=False,
            word_count=len(words),
            purpose=RecoveryPhrasePurpose.BASTION_ACCESS_RECOVERY.value,
            reason="invalid_recovery_phrase_word_count",
        )
    return RecoveryPhraseValidationResult(
        valid=True,
        word_count=len(words),
        purpose=RecoveryPhrasePurpose.BASTION_ACCESS_RECOVERY.value,
    )


def reject_bitcoin_wallet_seed_warning(phrase: str) -> None:
    lowered = phrase.lower()
    forbidden_markers = (
        "bitcoin_seed",
        "wallet_seed",
        "bitcoin private key",
        "private_key",
        "wallet private key",
        "xprv",
    )
    if any(marker in lowered for marker in forbidden_markers):
        raise ValueError("bitcoin_seed_input_rejected")
    if any(pattern.search(phrase) for pattern in _BITCOIN_PRIVATE_KEY_PATTERNS):
        raise ValueError("bitcoin_private_key_input_rejected")
    words = _split_words(phrase)
    if len(words) in {12, 15, 18, 21, 24} and words and all(
        word in _COMMON_BITCOIN_SEED_WORDS for word in words
    ):
        raise ValueError("bitcoin_seed_input_rejected")


def _word_count(strength: RecoveryPhraseStrength) -> int:
    if strength == RecoveryPhraseStrength.WORDS_12:
        return 12
    if strength == RecoveryPhraseStrength.WORDS_24:
        return 24
    raise ValueError("unsupported_recovery_phrase_strength")


def _normalize_phrase(phrase: str) -> str:
    return " ".join(_split_words(phrase))


def _split_words(phrase: str) -> list[str]:
    return [word for word in re.split(r"\s+", phrase.strip().lower()) if word]
