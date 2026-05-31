from difflib import SequenceMatcher

from app.services.news.deduplication.hashing import normalize_title
from app.services.news.deduplication.schemas import SimilarityResult


def _jaccard(a: str, b: str) -> float:
    sa = set(a.split())
    sb = set(b.split())
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / max(1, len(sa | sb))


def calculate_similarity(article_a: dict[str, str], article_b: dict[str, str]) -> SimilarityResult:
    reasons: list[str] = []
    if article_a.get("canonical_url_hash") and article_a.get("canonical_url_hash") == article_b.get("canonical_url_hash"):
        reasons.append("canonical_url_hash")
    if article_a.get("content_hash") and article_a.get("content_hash") == article_b.get("content_hash"):
        reasons.append("content_hash")
    ta = normalize_title(article_a.get("title", ""))
    tb = normalize_title(article_b.get("title", ""))
    seq = SequenceMatcher(None, ta, tb).ratio()
    jac = _jaccard(ta, tb)
    score = round((seq * 0.6 + jac * 0.4), 4)
    exact = "canonical_url_hash" in reasons or "content_hash" in reasons
    near = (score >= 0.8) and not exact
    if near:
        reasons.append("title_similarity")
    return SimilarityResult(exact, near, score, reasons, confidence=score)
