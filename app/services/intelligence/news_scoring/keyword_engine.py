from collections.abc import Iterable

from .constants import BITCOIN_KEYWORDS


def _score_text(text: str, keywords: Iterable[str]) -> float:
    lowered = text.lower()
    hits = sum(1 for k in keywords if k in lowered)
    return min(1.0, hits / max(1, len(tuple(keywords)) * 0.2))


def score_keywords(title: str, summary: str, content: str, keyword_set: set[str]) -> float:
    t = _score_text(title, keyword_set)
    s = _score_text(summary, keyword_set)
    c = _score_text(content, keyword_set)
    return min(1.0, (t * 0.55) + (s * 0.30) + (c * 0.15))


def btc_keyword_score(title: str, summary: str, content: str) -> float:
    return score_keywords(title, summary, content, BITCOIN_KEYWORDS)
