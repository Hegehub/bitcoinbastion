from sqlalchemy.orm import Session

from app.db.models.news_article import NewsArticle
from app.db.models.news_narrative_tag import NewsNarrativeTag
from app.db.models.news_score import NewsScore
from app.services.intelligence.news_scoring.scoring_service import NewsScoringService


class ProductionNewsScoringService:
    def __init__(self) -> None:
        self._svc = NewsScoringService()

    def classify_narratives(self, article: NewsArticle) -> list[dict[str, object]]:
        text = f"{article.title} {article.summary} {article.content_text}".lower()
        tag_map = {
            "ETF": ["etf", "issuer", "blackrock", "fidelity"],
            "macro": ["fed", "cpi", "inflation", "rates"],
            "security": ["hack", "exploit", "malware", "phishing"],
            "Lightning": ["lightning", "lnurl", "channel"],
            "mining": ["mining", "hashrate", "asic"],
            "sovereignty": ["self-custody", "privacy", "local node"],
            "volatility": ["volatility", "liquidation"],
        }
        out: list[dict[str, object]] = []
        for tag, kws in tag_map.items():
            hits = [k for k in kws if k in text]
            if hits:
                out.append({"tag": tag, "confidence": min(1.0, len(hits) / 3), "evidence_keywords": hits})
        return out

    def score_article(self, db: Session, article: NewsArticle) -> NewsScore:
        score = self._svc.score_article(db, article)
        for n in self.classify_narratives(article):
            c_raw = n.get("confidence")
            c_val = float(c_raw) if isinstance(c_raw, (int, float)) else 0.0
            db.add(NewsNarrativeTag(article_id=article.id, event_id=None, tag=str(n.get("tag", "unknown")), confidence=c_val, evidence_keywords_json={"keywords": n.get("evidence_keywords", [])}))
        return score

    def build_score_breakdown(self, score: NewsScore) -> dict[str, object]:
        return {"scores": score.factor_breakdown_json, "limitations": score.limitations_json}

    def classify_sentiment(self, article: NewsArticle) -> dict[str, object]:
        sentiment_score, sentiment_label, hits = self._svc.sentiment.analyze(article.title, article.summary, article.content_text)
        return {"sentiment_score": sentiment_score, "sentiment_label": sentiment_label, "hits": hits}

    def score_event(self, db: Session, event_id: int) -> dict[str, object]:
        return {"event_id": event_id, "limitations": ["Correlation is not proof of causation.", "Scores are informational and evidence-based."]}
