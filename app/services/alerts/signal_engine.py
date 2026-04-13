import json
from datetime import UTC, datetime

from app.db.models.news import NewsArticle
from app.db.models.onchain import OnchainEvent
from app.db.models.signal import Signal


class SignalEngine:
    def from_news(self, article: NewsArticle, explainability: dict[str, str | float]) -> Signal:
        score = (article.btc_relevance_score * 0.5) + (article.impact_score * 0.3) + (article.urgency_score * 0.2)
        return Signal(
            signal_type="news",
            severity=self._severity(score),
            score=score,
            confidence=article.confidence_score,
            title=article.title,
            summary=article.summary or article.content_clean[:220],
            details_json=json.dumps({"article_id": article.id, "url": article.url}),
            explainability_json=json.dumps(explainability),
            source_refs_json=json.dumps([article.url]),
            created_at=datetime.now(UTC),
        )

    def from_onchain_event(self, event: OnchainEvent) -> Signal:
        return Signal(
            signal_type="onchain",
            severity=self._severity(event.significance_score),
            score=event.significance_score,
            confidence=0.8,
            title=f"On-chain alert: {event.event_type}",
            summary=f"{event.event_type} observed for tx {event.txid[:12]}",
            details_json=json.dumps({"event_id": event.id, "provider": event.provider}),
            explainability_json=json.dumps({"tags": event.tags}),
            source_refs_json=json.dumps([event.txid]),
        )

    @staticmethod
    def _severity(score: float) -> str:
        if score >= 0.75:
            return "high"
        if score >= 0.4:
            return "medium"
        return "low"
