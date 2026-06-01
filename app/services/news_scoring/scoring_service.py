import time
from datetime import UTC, datetime
from pathlib import Path

import yaml  # type: ignore[import-untyped]

from app.db.models.news_article import NewsArticle
from app.db.models.news_article_score import NewsArticleScore
from app.db.models.news_event import NewsEvent
from .local_sentiment_engine import LocalSentimentEngine


class NewsScoringService:
    def __init__(self) -> None:
        self.sentiment_engine = LocalSentimentEngine()
        self.config = yaml.safe_load(Path("config/news_scoring.yaml").read_text())

    def _keyword_score(self, text: str, keys: set[str]) -> float:
        t = text.lower()
        hits = sum(1 for k in keys if k in t)
        return min(1.0, hits / 4)

    def score_article(self, article: NewsArticle) -> NewsArticleScore:
        started = time.perf_counter()
        text = f"{article.title} {article.summary} {article.content_text}"
        s = self.sentiment_engine
        sent = s.score(article.title, article.summary, article.content_text)
        btc_keys = {"bitcoin","btc","lightning","bitcoin core","etf","halving","mining","node","self-custody","on-chain","taproot","mempool"}
        btc = self._keyword_score(text, btc_keys)
        inst = self._keyword_score(text, s.institutional_keywords)
        macro = self._keyword_score(text, s.macro_keywords)
        reg = self._keyword_score(text, s.regulatory_keywords)
        sec = self._keyword_score(text, s.security_keywords)
        sov = self._keyword_score(text, s.sovereignty_keywords)
        urg = self._keyword_score(text, s.urgency_keywords)
        impact = max(inst, macro, reg, sec)
        conf = self.calculate_confidence(article.provider_confidence, btc, [inst, macro, reg, sec], article.published_at)
        breakdown = self.build_factor_breakdown(btc, impact, inst, macro, reg, sec, sov, sent.factors)
        limitations = self.build_limitations(conf)
        model = NewsArticleScore(
            article_id=article.id,
            event_id=None,
            btc_relevance_score=btc,
            market_impact_score=impact,
            urgency_score=urg,
            sentiment_score=sent.sentiment_score,
            source_credibility_score=article.provider_confidence,
            institutional_score=inst,
            macro_score=macro,
            regulatory_score=reg,
            security_risk_score=sec,
            sovereignty_score=sov,
            confidence_score=conf,
            sentiment_label=sent.label,
            risk_band=self.derive_risk_band(sec, macro, reg, conf),
            score_version=self.config["score_version"],
            scoring_method=self.config["scoring_method"],
            explanation_json={"summary": "Correlation is not proof of causation."},
            factor_breakdown_json=breakdown,
            limitations_json=limitations,
        )
        duration_ms = int((time.perf_counter() - started) * 1000)
        print({"event":"news_scoring.completed","article_id":article.id,"duration_ms":duration_ms,"score_version":model.score_version,"confidence_score":conf})
        return model

    def score_event(self, event: NewsEvent) -> dict[str, float | str]:
        return {"event_id": event.id, "market_impact_score": event.market_impact_score, "confidence_score": event.event_confidence}

    def calculate_confidence(self, source_cred: float, keyword_density: float, cats: list[float], published_at: datetime) -> float:
        freshness = 1.0 if (datetime.now(UTC).replace(tzinfo=None) - published_at).days < 2 else 0.6
        category_agreement = sum(1 for c in cats if c > 0.4) / max(1, len(cats))
        return max(0.0, min(1.0, 0.30*source_cred + 0.20*keyword_density + 0.20*category_agreement + 0.15*keyword_density + 0.10*freshness + 0.05*0.5))

    def build_factor_breakdown(self, btc: float, impact: float, inst: float, macro: float, reg: float, sec: float, sov: float, sentiment_factors: list[str]) -> dict[str, object]:
        return {"btc_relevance":[f"score={btc:.2f}"],"market_impact":[f"score={impact:.2f}"],"categories":{"institutional":inst,"macro":macro,"regulatory":reg,"security":sec,"sovereignty":sov},"sentiment":sentiment_factors}

    def build_limitations(self, confidence: float) -> dict[str, object]:
        items=["Rule-based scoring may miss nuance.","No external ML model used.","Correlation is not proof of causation.","Provider corroboration not yet available."]
        if confidence < 0.45:
            items.append("Low confidence due to weak/ambiguous indicators.")
        return {"limitations": items}

    def derive_risk_band(self, security: float, macro: float, regulatory: float, confidence: float) -> str:
        if confidence < 0.3:
            return "UNKNOWN"
        if security >= 0.9:
            return "CRITICAL"
        if security >= 0.8:
            return "HIGH"
        if max(macro, regulatory) >= 0.7:
            return "HIGH"
        if max(macro, regulatory, security) >= 0.45:
            return "MEDIUM"
        return "LOW"
