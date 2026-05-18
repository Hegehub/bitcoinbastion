import json
from datetime import UTC, datetime
from time import perf_counter

from app.db.models.news import NewsArticle
from app.db.models.onchain import OnchainEvent
from app.db.models.signal import Signal
from app.core.telemetry import observe_signal_latency
from app.services.blockchain.chain_state_service import ChainStateService
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

        onchain_explainability = self._decode_object(event.explainability_json)
        raw_payload = self._decode_object(event.raw_payload_json)

        tip_height = self._payload_int(raw_payload, "tip_height", default=max(1, int(event.block_height or 0) + 1))
        headers_height = self._payload_int(raw_payload, "headers_height", default=tip_height)
        provider_tip_height: int | None = self._payload_int(raw_payload, "provider_tip_height", default=0) or None
        provider_confidence = self._payload_float(raw_payload, "provider_confidence", default=0.0) or None
        provider_data_age_seconds: int | None = self._payload_int(
            raw_payload, "provider_data_age_seconds", default=-1
        )
        if provider_data_age_seconds is not None and provider_data_age_seconds < 0:
            provider_data_age_seconds = None
        chain_source = str(raw_payload.get("chain_state_source", "repository_fallback"))

        chain_state = ChainStateService().evaluate(
            tip_height=tip_height,
            observed_block_height=max(0, int(event.block_height or 0)),
            headers_height=headers_height,
            provider_tip_height=provider_tip_height,
            provider_confidence=provider_confidence,
            provider_data_age_seconds=provider_data_age_seconds,
            data_source=chain_source,
        )

        base_confidence = max(0.0, min(1.0, float(event.confidence_score or 0.0)))
        adjusted_confidence = base_confidence
        confidence_penalty = 0.0
        publishable = True
        if chain_state.finality_band == "weak":
            confidence_penalty += 0.2
            publishable = base_confidence >= 0.75 and event.significance_score >= 0.7
        elif chain_state.finality_band == "moderate":
            confidence_penalty += 0.08

        confidence_penalty += min(0.12, chain_state.reorg_risk_score * 0.1)
        adjusted_confidence = round(max(0.05, adjusted_confidence - confidence_penalty), 4)

        severity = self._severity(event.significance_score)
        if chain_state.finality_band == "weak" and severity == "high":
            severity = "medium"

        recommendations = [
            "Track subsequent confirmations before irreversible action.",
        ]
        if chain_state.finality_band == "weak":
            recommendations.append("Delay high-impact automation until finality reaches moderate or strong.")
        elif chain_state.finality_band == "moderate":
            recommendations.append("Re-check chain-state in next blocks for stronger finality.")

        draft = Signal(
            signal_type="onchain",
            severity=severity,
            score=event.significance_score,
            confidence=adjusted_confidence,
            title=f"On-chain alert: {event.event_type}",
            summary=f"{event.event_type} observed for tx {event.txid[:12]}",
            details_json=json.dumps(
                {
                    "event_id": event.id,
                    "provider": event.provider,
                    "chain_state": {
                        "finality_band": chain_state.finality_band,
                        "reorg_risk_score": chain_state.reorg_risk_score,
                        "confidence_score": chain_state.confidence_score,
                        "freshness": chain_state.freshness,
                    },
                }
            ),
            source_refs_json=json.dumps([event.txid]),
            is_published=publishable,
        )
        tags = self._decode_list(event.tags_json)

        source_id = self.onchain_source_id(event)
        horizons = SignalHorizonService().build(draft)
        draft.explainability_json = json.dumps(
            {
                "reason": "onchain_scoring_pipeline",
                "source_type": "onchain_event",
                "source_id": source_id,
                "onchain_score_explainability": onchain_explainability,
                "tags": tags,
                "chain_state": {
                    "finality_band": chain_state.finality_band,
                    "finality_score": chain_state.finality_score,
                    "reorg_risk_score": chain_state.reorg_risk_score,
                    "confidence_score": chain_state.confidence_score,
                    "freshness": chain_state.freshness,
                    "risk_components": chain_state.explainability.get("risk_components", {}),
                    "contribution": {
                        "confidence_penalty": round(confidence_penalty, 4),
                        "severity_adjusted": chain_state.finality_band == "weak",
                        "publishable": publishable,
                    },
                },
                "recommendations": recommendations,
                "horizons": horizons,
                "horizon": horizons["dominant"],
            }
        )
        observe_signal_latency(source="onchain", duration_seconds=perf_counter() - started_at)
        return draft

    @staticmethod
    def _decode_list(raw: str) -> list[object]:
        try:
            parsed = json.loads(raw or "[]")
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []

    @staticmethod
    def _decode_object(raw: str) -> dict[str, object]:
        try:
            parsed = json.loads(raw or "{}")
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _payload_int(payload: dict[str, object], key: str, *, default: int) -> int:
        value = payload.get(key, default)
        if isinstance(value, bool):
            return default
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str) and value.strip().lstrip("-").isdigit():
            return int(value)
        return default

    @staticmethod
    def _payload_float(payload: dict[str, object], key: str, *, default: float) -> float:
        value = payload.get(key, default)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return default
        return default

    @staticmethod
    def _severity(score: float) -> str:
        if score >= 0.75:
            return "high"
        if score >= 0.4:
            return "medium"
        return "low"
