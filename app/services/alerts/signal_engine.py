import json
from datetime import UTC, datetime
from time import perf_counter

from app.db.models.news import NewsArticle
from app.db.models.onchain import OnchainEvent
from app.db.models.signal import Signal
from app.core.telemetry import observe_signal_latency
from app.services.horizons.signal_horizon_service import SignalHorizonService


class SignalEngine:
    @staticmethod
    def onchain_source_id(event: OnchainEvent) -> str:
        txid = (event.txid or "").strip()
        event_type = (event.event_type or "unknown").strip()
        block_height = int(event.block_height or 0)
        if txid:
            return f"{txid}:{event_type}:{block_height}"
        return f"event:{event.id or 0}:{event_type}:{block_height}"

    def from_news(self, article: NewsArticle, explainability: dict[str, str | float]) -> Signal:
        started_at = perf_counter()
        score = (
            (article.btc_relevance_score * 0.5)
            + (article.impact_score * 0.3)
            + (article.urgency_score * 0.2)
        )
        draft = Signal(
            signal_type="news",
            severity=self._severity(score),
            score=score,
            confidence=article.confidence_score,
            title=article.title,
            summary=article.summary or article.content_clean[:220],
            details_json=json.dumps({"article_id": article.id, "url": article.url}),
            source_refs_json=json.dumps([article.url]),
            created_at=datetime.now(UTC),
        )
        horizons = SignalHorizonService().build(draft)
        draft.explainability_json = json.dumps(
            {**explainability, "horizons": horizons, "horizon": horizons["dominant"]}
        )
        observe_signal_latency(source="news", duration_seconds=perf_counter() - started_at)
        return draft

    def from_onchain_event(self, event: OnchainEvent) -> Signal:
        started_at = perf_counter()
        draft = Signal(
            signal_type="onchain",
            severity=self._severity(event.significance_score),
            score=event.significance_score,
            confidence=event.confidence_score,
            title=f"On-chain alert: {event.event_type}",
            summary=f"{event.event_type} observed for tx {event.txid[:12]}",
            details_json=json.dumps({"event_id": event.id, "provider": event.provider}),
            source_refs_json=json.dumps([event.txid]),
        )
        try:
            tags = json.loads(event.tags_json or "[]")
        except json.JSONDecodeError:
            tags = []
        try:
            onchain_explainability = json.loads(event.explainability_json or "{}")
            if not isinstance(onchain_explainability, dict):
                onchain_explainability = {}
        except json.JSONDecodeError:
            onchain_explainability = {}

        source_id = self.onchain_source_id(event)
        horizons = SignalHorizonService().build(draft)
        draft.explainability_json = json.dumps(
            {
                "reason": "onchain_scoring_pipeline",
                "source_type": "onchain_event",
                "source_id": source_id,
                "onchain_score_explainability": onchain_explainability,
                "tags": tags,
                "horizons": horizons,
                "horizon": horizons["dominant"],
            }
        )
        observe_signal_latency(source="onchain", duration_seconds=perf_counter() - started_at)
        return draft

    @staticmethod
    def _severity(score: float) -> str:
        if score >= 0.75:
            return "high"
        if score >= 0.4:
            return "medium"
        return "low"
