from datetime import UTC, datetime

from prometheus_client import Counter, Histogram
from sqlalchemy.orm import Session

from app.db.models.news_article import NewsArticle
from app.db.models.news_score import NewsScore
from app.db.models.scoring_factor import ScoringFactor
from app.db.models.score_explanation import ScoreExplanation
from .confidence_engine import compute_confidence
from .explanation_builder import build_explanation
from .keyword_profiles import KEYWORD_PROFILES
from .sentiment_engine import SentimentEngine

NEWS_SCORING_TOTAL = Counter("news_scoring_total", "Total news scoring operations")
NEWS_SCORING_FAILURES_TOTAL = Counter("news_scoring_failures_total", "Total failures")
NEWS_SCORING_DURATION_SECONDS = Histogram("news_scoring_duration_seconds", "Duration")
NEWS_SENTIMENT_DISTRIBUTION = Counter("news_sentiment_distribution", "Sentiment labels", ["label"])
NEWS_HIGH_IMPACT_TOTAL = Counter("news_high_impact_total", "High impact news articles")


class NewsScoringService:
    def __init__(self) -> None:
        self.sentiment = SentimentEngine()

    def _score_category(self, text: str, category: str) -> tuple[float, list[str]]:
        lowered = text.lower()
        hits = [k for k in KEYWORD_PROFILES[category] if k in lowered]
        return min(1.0, len(hits) / 4), hits

    def score_article(self, db: Session, article: NewsArticle) -> NewsScore:
        NEWS_SCORING_TOTAL.inc()
        with NEWS_SCORING_DURATION_SECONDS.time():
            try:
                text = f"{article.title} {article.summary} {article.content_text}"
                sentiment_score, sentiment_label, sentiment_hits = self.sentiment.analyze(
                    article.title, article.summary, article.content_text
                )
                btc, btc_hits = self._score_category(text, "bitcoin_core")
                lightning, lightning_hits = self._score_category(text, "lightning")
                mining, mining_hits = self._score_category(text, "mining")
                institutional, institutional_hits = self._score_category(text, "institutional")
                macro, macro_hits = self._score_category(text, "macro")
                regulatory, regulatory_hits = self._score_category(text, "regulatory")
                security, security_hits = self._score_category(text, "security")
                sovereignty, sovereignty_hits = self._score_category(text, "sovereignty")
                urgency, urgency_hits = self._score_category(text, "volatility")
                btc_relevance = max(btc, lightning, mining, institutional)
                market_impact = max(institutional, macro, regulatory, security)
                source_cred = article.provider_confidence
                freshness = (
                    1.0
                    if (datetime.now(UTC).replace(tzinfo=None) - article.published_at).days <= 1
                    else 0.7
                )
                completeness = 1.0 if article.content_text else 0.5
                category_conf = (
                    sum(v for v in [institutional, macro, regulatory, security] if v > 0.4) / 4
                )
                confidence = compute_confidence(
                    source_cred, btc_relevance, category_conf, freshness, completeness, source_cred
                )
                top = []
                if institutional_hits:
                    top.append("Detected institutional ETF/fund-related keywords.")
                if btc_relevance >= 0.6:
                    top.append("Strong Bitcoin relevance detected.")
                if security_hits:
                    top.append("Security-risk language detected.")
                explanation = build_explanation(
                    top or ["Limited strong category signals detected."]
                )
                row = NewsScore(
                    article_id=article.id,
                    btc_relevance_score=btc_relevance,
                    market_impact_score=market_impact,
                    urgency_score=urgency,
                    sentiment_score=sentiment_score,
                    source_credibility_score=source_cred,
                    institutional_score=institutional,
                    macro_score=macro,
                    regulatory_score=regulatory,
                    security_risk_score=security,
                    sovereignty_score=sovereignty,
                    novelty_score=0.2 if article.is_duplicate else 0.85,
                    confidence_score=confidence,
                    provider_confidence=source_cred,
                    explanation_json=explanation,
                    factor_breakdown_json={
                        "keywords_detected": {
                            "btc": btc_hits,
                            "lightning": lightning_hits,
                            "mining": mining_hits,
                            "institutional": institutional_hits,
                            "macro": macro_hits,
                            "regulatory": regulatory_hits,
                            "security": security_hits,
                            "sovereignty": sovereignty_hits,
                            "urgency": urgency_hits,
                        },
                        "sentiment_hits": sentiment_hits,
                    },
                    limitations_json={"limitations": explanation["limitations"]},
                    low_confidence=confidence < 0.4,
                    high_uncertainty=sentiment_label == "UNCERTAIN",
                )
                db.add(row)
                db.flush()
                for factor, value in [
                    ("btc_relevance", btc_relevance),
                    ("market_impact", market_impact),
                    ("institutional", institutional),
                    ("macro", macro),
                    ("regulatory", regulatory),
                    ("security", security),
                    ("sovereignty", sovereignty),
                    ("confidence", confidence),
                ]:
                    db.add(
                        ScoringFactor(
                            score_id=row.id,
                            factor=factor,
                            weight=float(value),
                            explanation=f"{factor} contribution",
                        )
                    )
                db.add(
                    ScoreExplanation(
                        score_id=row.id,
                        summary="High Bitcoin relevance scoring with explainable factors.",
                        key_factors_json=top,
                        limitations_json=explanation["limitations"],
                    )
                )
                if market_impact >= 0.75:
                    NEWS_HIGH_IMPACT_TOTAL.inc()
                NEWS_SENTIMENT_DISTRIBUTION.labels(label=sentiment_label).inc()
                return row
            except Exception:
                NEWS_SCORING_FAILURES_TOTAL.inc()
                raise
