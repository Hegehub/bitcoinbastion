from dataclasses import dataclass
from datetime import UTC, datetime

from app.db.models.news import NewsArticle, NewsSource

BITCOIN_KEYWORDS = {"bitcoin", "btc", "halving", "lightning", "mining", "utxo", "etf"}
URGENT_KEYWORDS = {"hack", "ban", "break", "exploit", "liquidation", "surge"}


@dataclass
class ScoreResult:
    relevance: float
    urgency: float
    impact: float
    confidence: float
    explainability: dict[str, str | float]


class NewsScoringService:
    def score(self, article: NewsArticle, source: NewsSource) -> ScoreResult:
        text = f"{article.title} {article.content_clean}".lower()
        word_set = set(text.split())

        relevance_matches = len(word_set.intersection(BITCOIN_KEYWORDS))
        urgency_matches = len(word_set.intersection(URGENT_KEYWORDS))

        relevance = min(1.0, relevance_matches / 3)
        urgency = min(1.0, urgency_matches / 2)
        freshness = self._freshness(article.published_at)
        impact = min(1.0, (0.6 * relevance) + (0.4 * freshness))
        confidence = min(1.0, (source.credibility_weight * 0.7) + (relevance * 0.3))

        return ScoreResult(
            relevance=relevance,
            urgency=urgency,
            impact=impact,
            confidence=confidence,
            explainability={
                "keyword_matches": float(relevance_matches),
                "urgent_matches": float(urgency_matches),
                "freshness": freshness,
                "credibility_weight": source.credibility_weight,
            },
        )

    @staticmethod
    def _freshness(published_at: datetime) -> float:
        age_hours = max(1.0, (datetime.now(UTC) - published_at).total_seconds() / 3600)
        return max(0.0, min(1.0, 24 / age_hours / 24))
