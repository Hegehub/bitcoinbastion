from .constants import INSTITUTIONAL_KEYWORDS, MACRO_KEYWORDS, REGULATORY_KEYWORDS, SECURITY_KEYWORDS, SOVEREIGNTY_KEYWORDS
from .keyword_engine import score_keywords


def calculate_factor_scores(title: str, summary: str, content: str) -> dict[str, float]:
    return {
        "institutional_score": score_keywords(title, summary, content, INSTITUTIONAL_KEYWORDS),
        "macro_score": score_keywords(title, summary, content, MACRO_KEYWORDS),
        "regulatory_score": score_keywords(title, summary, content, REGULATORY_KEYWORDS),
        "security_risk_score": score_keywords(title, summary, content, SECURITY_KEYWORDS),
        "sovereignty_score": score_keywords(title, summary, content, SOVEREIGNTY_KEYWORDS),
    }
