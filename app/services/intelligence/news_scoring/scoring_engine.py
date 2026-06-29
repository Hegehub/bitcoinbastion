from sqlalchemy.orm import Session

from app.db.models.news_article import NewsArticle
from app.db.models.news_event import NewsEvent
from app.db.models.news_score import NewsScore
from .confidence_engine import calculate_confidence
from .constants import NEGATIVE_KEYWORDS, POSITIVE_KEYWORDS, SCORE_VERSION
from .factor_engine import calculate_factor_scores
from .keyword_engine import btc_keyword_score, score_keywords
from .reason_engine import build_explanation, build_limitations


class NewsScoringEngine:
    def score_article(self, db: Session, article: NewsArticle) -> NewsScore:
        factors = calculate_factor_scores(article.title, article.summary, article.content_text)
        btc = btc_keyword_score(article.title, article.summary, article.content_text)
        pos = score_keywords(
            article.title, article.summary, article.content_text, POSITIVE_KEYWORDS
        )
        neg = score_keywords(
            article.title, article.summary, article.content_text, NEGATIVE_KEYWORDS
        )
        sentiment = max(0.0, min(1.0, 0.5 + (pos - neg) / 2))
        novelty = 0.2 if article.is_duplicate else 0.85
        source_cred = max(0.0, min(1.0, article.provider_confidence))
        market_impact = max(
            factors["institutional_score"],
            factors["macro_score"],
            factors["regulatory_score"],
            factors["security_risk_score"],
        )
        confidence = calculate_confidence(article.provider_confidence, source_cred, novelty)
        scores = {
            "btc_relevance_score": btc,
            "market_impact_score": market_impact,
            "urgency_score": market_impact,
            "sentiment_score": sentiment,
            "source_credibility_score": source_cred,
            "novelty_score": novelty,
            "confidence_score": confidence,
            **factors,
        }
        model = NewsScore(
            article_id=article.id,
            event_id=None,
            provider_confidence=article.provider_confidence,
            score_version=SCORE_VERSION,
            explanation_json=build_explanation(scores),
            factor_breakdown_json=scores,
            limitations_json=build_limitations(article.provider_confidence),
            low_confidence=confidence < 0.4,
            high_uncertainty=confidence < 0.5,
            **scores,
        )
        db.add(model)
        return model

    def score_event(self, db: Session, event: NewsEvent) -> NewsScore:
        # event-level aggregation placeholder using existing event fields
        s = NewsScore(
            article_id=None,
            event_id=event.id,
            btc_relevance_score=event.btc_relevance_score,
            market_impact_score=event.market_impact_score,
            urgency_score=event.market_impact_score,
            sentiment_score=0.5,
            source_credibility_score=event.provider_confidence,
            institutional_score=1.0 if event.is_institutional_related else 0.0,
            macro_score=1.0 if event.is_macro_related else 0.0,
            regulatory_score=1.0 if event.is_regulatory_related else 0.0,
            security_risk_score=1.0 if event.is_security_related else 0.0,
            sovereignty_score=0.0,
            novelty_score=max(0.1, min(1.0, 1.0 / max(1, event.article_count))),
            confidence_score=event.event_confidence,
            provider_confidence=event.provider_confidence,
            score_version=SCORE_VERSION,
            explanation_json={
                "summary": "Event score is aggregated from linked article and event metadata."
            },
            factor_breakdown_json={
                "event_article_count": event.article_count,
                "event_source_count": event.source_count,
            },
            limitations_json={
                "limitations": ["Event scoring is aggregated and may hide article-level nuances."]
            },
        )
        db.add(s)
        return s
