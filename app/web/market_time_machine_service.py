from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db.models.btc_candle import BTCCandle
from app.db.models.candle_attribution_candidate import CandleAttributionCandidate
from app.db.models.evidence_packet import EvidenceArtifact, EvidencePacket, EvidenceReplayLog
from app.db.models.intelligence_signals import IntelligenceOperatorReview, IntelligenceSignalCandidate
from app.db.models.intelligence_timeline import IntelligenceTimelineEvent
from app.db.models.narrative_memory_snapshot import NarrativeMemorySnapshot
from app.db.models.news_article import NewsArticle
from app.db.models.news_event import NewsEvent
from app.db.models.news_price_impact import NewsPriceImpact
from app.db.models.news_source import NewsSource
from app.db.models.source_reputation_profile import SourceReputationProfile
from app.schemas.market_time_machine_web import (
    CandleAttributionDTO,
    EvidencePanelDTO,
    MarketTimelineDTO,
    NewsMarkerDTO,
    ReplaySummaryDTO,
    SignalCardDTO,
)

SAFETY_LIMITATIONS = [
    "Correlation is not proof of causation.",
    "Bitcoin Bastion provides evidence-based informational analysis.",
    "Nothing displayed here constitutes financial advice.",
    "Provider degradation, missing evidence, and low confidence must remain visible.",
]

TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"]
FILTERS = [
    "all",
    "news",
    "candles",
    "signals",
    "security",
    "regulatory",
    "institutional",
    "etf",
    "macro",
    "mining",
    "lightning",
    "positive",
    "negative",
    "high_confidence",
    "operator_reviewed",
    "operator_actions",
]


class MarketTimeMachineWebService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def dashboard(self, *, timeframe: str = "1h", page_size: int = 80) -> MarketTimelineDTO:
        timeframe = timeframe if timeframe in TIMEFRAMES else "1h"
        candles = self.candles(timeframe=timeframe, limit=min(max(page_size, 10), 200))
        timeline = self.timeline(page_size=50)
        markers = self.news_markers(limit=120)
        narratives = self.narrative_panel(limit=9)
        similarity_preview = self.similarity_panel(limit=5)
        return MarketTimelineDTO(
            timeline_items=timeline.timeline_items,
            chart_markers=markers,
            candles=candles,
            signals=[SignalCardDTO(title="No candidate signals currently available.", status="empty")],
            page=1,
            page_size=50,
            has_next=timeline.has_next,
            filters={"timeframe": timeframe, "available_timeframes": TIMEFRAMES, "available_filters": FILTERS},
            limitations=SAFETY_LIMITATIONS,
            evidence_summary={"available": True, "source": "backend_dto", "missing_evidence_visible": True},
            confidence_breakdown={"provider": "backend", "attribution": "backend", "similarity": "backend"},
            narrative_strength=narratives,
            similarity_preview=similarity_preview,
            operator_status={"operator_reviewed": False, "status": "display_only"},
        )


    def landing_payload(self, *, timeframe: str = "1h") -> dict[str, object]:
        dashboard = self.dashboard(timeframe=timeframe, page_size=80)
        latest_candle = dashboard.candles[-1].model_dump() if dashboard.candles else None
        latest_event = dashboard.chart_markers[0].model_dump() if dashboard.chart_markers else None
        signals = self.signal_summary(limit=25)
        evidence = self.evidence_summary(limit=25)
        replay = self.replay_requests_summary(limit=25)
        sources = self.source_summary(limit=50)
        return {
            "market_timeline": dashboard.model_dump(),
            "btc_price": {
                "price_usd": latest_candle.get("close") if latest_candle else None,
                "timeframe": latest_candle.get("timeframe") if latest_candle else timeframe,
                "observed_at": latest_candle.get("close_time") if latest_candle else "unknown",
                "provider_confidence": latest_candle.get("provider_confidence") if latest_candle else 0.0,
            },
            "latest_high_impact_event": latest_event,
            "latest_published_signal": signals["latest_published_signal"],
            "operator_queue": signals["operator_queue"],
            "evidence_replay_requests": replay,
            "source_summary": sources,
            "signal_summary": signals,
            "evidence_summary": evidence,
            "limitations": SAFETY_LIMITATIONS,
        }

    def signal_summary(self, *, limit: int = 50, status: str | None = None) -> dict[str, object]:
        query = select(IntelligenceSignalCandidate)
        if status and status != "all":
            query = query.where(IntelligenceSignalCandidate.status == status)
        rows = list(
            self.db.execute(
                query.order_by(IntelligenceSignalCandidate.created_at.desc(), IntelligenceSignalCandidate.id.desc()).limit(min(max(limit, 1), 100))
            ).scalars()
        )
        counts = {name: 0 for name in ["published", "pending_review", "held", "rejected", "false_positive", "expired"]}
        for row in rows:
            counts[self._signal_bucket(row)] = counts.get(self._signal_bucket(row), 0) + 1
        pending_ids = [row.id for row in rows if row.requires_operator_review or self._signal_bucket(row) == "pending_review"]
        reviews = list(
            self.db.execute(
                select(IntelligenceOperatorReview)
                .where(IntelligenceOperatorReview.signal_candidate_id.in_(pending_ids or [0]))
                .order_by(IntelligenceOperatorReview.created_at.desc())
                .limit(25)
            ).scalars()
        )
        items = [
            {
                "id": row.id,
                "title": row.title or f"Signal {row.id}",
                "status": self._signal_bucket(row),
                "raw_status": row.status,
                "confidence": row.confidence_score or 0.0,
                "evidence_packet_id": row.evidence_packet_id,
                "requires_operator_review": row.requires_operator_review,
                "policy_decision": row.policy_decision,
                "published_at": self._dt(row.published_at),
                "created_at": self._dt(row.created_at),
                "limitations": SAFETY_LIMITATIONS,
            }
            for row in rows
        ]
        return {
            "items": items,
            "counts": counts,
            "latest_published_signal": next((item for item in items if item["status"] == "published"), items[0] if items else None),
            "operator_queue": {
                "pending_count": len(pending_ids),
                "reviews": [
                    {
                        "signal_candidate_id": review.signal_candidate_id,
                        "review_status": review.review_status,
                        "false_positive_marker": review.false_positive_marker,
                        "created_at": self._dt(review.created_at),
                    }
                    for review in reviews
                ],
            },
            "limitations": SAFETY_LIMITATIONS,
        }

    def evidence_summary(self, *, limit: int = 25) -> dict[str, object]:
        packets = list(
            self.db.execute(
                select(EvidencePacket).order_by(EvidencePacket.created_at.desc(), EvidencePacket.id.desc()).limit(min(max(limit, 1), 100))
            ).scalars()
        )
        packet_ids = [packet.id for packet in packets]
        artifacts = list(
            self.db.execute(
                select(EvidenceArtifact).where(EvidenceArtifact.packet_id.in_(packet_ids or [0])).limit(200)
            ).scalars()
        )
        artifact_counts: dict[int, int] = {}
        for artifact in artifacts:
            if artifact.packet_id is not None:
                artifact_counts[artifact.packet_id] = artifact_counts.get(artifact.packet_id, 0) + 1
        return {
            "items": [
                {
                    "packet_id": packet.id,
                    "title": packet.title or f"Evidence packet {packet.id}",
                    "summary": packet.summary or "Evidence packet summary unavailable.",
                    "packet_type": packet.packet_type,
                    "source_entity_type": packet.source_entity_type,
                    "source_entity_id": packet.source_entity_id,
                    "confidence": packet.confidence_score or 0.0,
                    "provider_confidence": packet.provider_confidence or 0.0,
                    "source_confidence": packet.source_confidence or 0.0,
                    "artifact_count": artifact_counts.get(packet.id, 0),
                    "replay_url": f"/market/evidence?packet_id={packet.id}",
                    "created_at": self._dt(packet.created_at),
                    "limitations": SAFETY_LIMITATIONS,
                }
                for packet in packets
            ],
            "limitations": SAFETY_LIMITATIONS + ([] if packets else ["No evidence packets available."]),
        }

    def replay_requests_summary(self, *, limit: int = 25) -> dict[str, object]:
        rows = list(
            self.db.execute(
                select(EvidenceReplayLog).order_by(EvidenceReplayLog.started_at.desc(), EvidenceReplayLog.id.desc()).limit(min(max(limit, 1), 100))
            ).scalars()
        )
        return {
            "items": [
                {
                    "entity_type": row.entity_type,
                    "entity_id": row.entity_id,
                    "step": row.step_name,
                    "input_hash": row.input_hash,
                    "output_hash": row.output_hash,
                    "success": row.success,
                    "error_code": row.error_code,
                    "started_at": self._dt(row.started_at),
                    "finished_at": self._dt(row.finished_at),
                    "policy_decisions": (row.metadata_json or {}).get("policy_decisions", []),
                    "operator_actions": (row.metadata_json or {}).get("operator_actions", []),
                    "publication_status": (row.metadata_json or {}).get("publication_status", "unknown"),
                }
                for row in rows
            ],
            "failure_count": sum(1 for row in rows if not row.success),
            "limitations": SAFETY_LIMITATIONS + ([] if rows else ["Replay unavailable."]),
        }

    def source_summary(self, *, limit: int = 50, sort: str = "name") -> dict[str, object]:
        rows = list(
            self.db.execute(select(NewsSource).order_by(NewsSource.name.asc()).limit(min(max(limit, 1), 100))).scalars()
        )
        source_ids = [row.id for row in rows]
        reputations = {
            row.source_id: row
            for row in self.db.execute(
                select(SourceReputationProfile).where(SourceReputationProfile.source_id.in_(source_ids or [0]))
            ).scalars()
        }
        items: list[dict[str, object]] = []
        for row in rows:
            reputation = reputations.get(row.id)
            items.append(
                {
                    "source_id": row.id,
                    "source_name": row.name,
                    "health": row.health_band or ("DEGRADED" if row.is_degraded else "UNKNOWN"),
                    "provider_confidence": row.provider_confidence,
                    "reputation": reputation.reliability_score if reputation else 0.0,
                    "average_latency": row.avg_latency_ms or 0.0,
                    "failure_count": row.failure_count,
                    "first_mover_score": reputation.first_mover_score if reputation else 0.0,
                    "signal_quality": reputation.signal_quality_score if reputation else row.signal_quality_weight,
                    "is_degraded": row.is_degraded,
                    "limitations": SAFETY_LIMITATIONS,
                }
            )
        if sort == "confidence":
            items.sort(key=lambda item: self._float_value(item.get("provider_confidence")), reverse=True)
        elif sort == "failures":
            items.sort(key=lambda item: self._int_value(item.get("failure_count")), reverse=True)
        elif sort == "quality":
            items.sort(key=lambda item: self._float_value(item.get("signal_quality")), reverse=True)
        return {
            "items": items,
            "provider_health": {
                "news_providers": len(items),
                "market_providers": 0,
                "provider_confidence": round(sum(self._float_value(item.get("provider_confidence")) for item in items) / len(items), 4) if items else 0.0,
                "degraded_sources": [str(item.get("source_name")) for item in items if bool(item.get("is_degraded"))],
                "degraded_count": sum(1 for item in items if bool(item.get("is_degraded"))),
                "provider_health_visible": True,
                "limitations": SAFETY_LIMITATIONS,
            },
            "limitations": SAFETY_LIMITATIONS + ([] if items else ["Source registry is empty or unavailable."]),
        }

    def timeline(
        self,
        *,
        event_type: str | None = None,
        filter_name: str = "all",
        filters: list[str] | None = None,
        page: int = 1,
        page_size: int = 50,
        sort: str = "desc",
        window: str = "24h",
    ) -> MarketTimelineDTO:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        active_filters = self._normalize_filters(filters or filter_name)
        filter_name = ",".join(active_filters) if active_filters else "all"
        query = select(IntelligenceTimelineEvent).where(IntelligenceTimelineEvent.is_deleted.is_(False))
        if event_type:
            query = query.where(IntelligenceTimelineEvent.event_type == event_type)
        for active_filter in active_filters:
            if active_filter != "all":
                query = self._apply_filter(query, active_filter)
        query = self._apply_window(query, window)
        order = IntelligenceTimelineEvent.event_time.asc() if sort == "asc" else IntelligenceTimelineEvent.event_time.desc()
        rows = list(
            self.db.execute(query.order_by(order, IntelligenceTimelineEvent.id.desc()).offset((page - 1) * page_size).limit(page_size + 1)).scalars()
        )
        return MarketTimelineDTO(
            timeline_items=[self._timeline_item(row) for row in rows[:page_size]],
            chart_markers=[],
            candles=[],
            page=page,
            page_size=page_size,
            has_next=len(rows) > page_size,
            filters={"filter": filter_name, "active_filters": active_filters, "sort": sort, "window": window, "available_filters": FILTERS},
            limitations=SAFETY_LIMITATIONS,
        )

    def candles(self, *, timeframe: str = "1h", limit: int = 120) -> list[CandleAttributionDTO]:
        timeframe = timeframe if timeframe in TIMEFRAMES else "1h"
        rows = list(
            self.db.execute(
                select(BTCCandle)
                .where(BTCCandle.timeframe == timeframe)
                .order_by(BTCCandle.open_time.desc(), BTCCandle.id.desc())
                .limit(min(max(limit, 1), 10000))
            ).scalars()
        )
        return [self.candle_attribution(row.id) for row in reversed(rows)]

    def candle_attribution(self, candle_id: int) -> CandleAttributionDTO:
        candle = self.db.get(BTCCandle, candle_id)
        if candle is None:
            return CandleAttributionDTO(
                id=candle_id,
                timeframe="unknown",
                open_time="unknown",
                close_time="unknown",
                limitations=SAFETY_LIMITATIONS + ["No attribution available."],
            )
        candidates = list(
            self.db.execute(
                select(CandleAttributionCandidate)
                .where(CandleAttributionCandidate.candle_id == candle_id)
                .order_by(CandleAttributionCandidate.normalized_score.desc(), CandleAttributionCandidate.id.asc())
                .limit(10)
            ).scalars()
        )
        event_ids = [c.event_id for c in candidates if c.event_id]
        article_ids = [c.article_id for c in candidates if c.article_id]
        events = {
            row.id: row
            for row in self.db.execute(select(NewsEvent).where(NewsEvent.id.in_(event_ids or [0]))).scalars()
        }
        articles = {
            row.id: row
            for row in self.db.execute(select(NewsArticle).where(NewsArticle.id.in_(article_ids or [0]))).scalars()
        }
        return CandleAttributionDTO(
            id=candle.id,
            timeframe=candle.timeframe,
            open_time=self._dt(candle.open_time),
            close_time=self._dt(candle.close_time),
            open=candle.open,
            high=candle.high,
            low=candle.low,
            close=candle.close,
            volume=candle.volume,
            price_change_pct=self._price_change(candle.open, candle.close),
            confidence=max([c.normalized_score for c in candidates] or [0.0]),
            provider_confidence=candle.provider_confidence,
            dominant_direction=self._dominant_direction(candle.open, candle.close),
            volatility_score=candle.volatility_score,
            attribution_count=len(candidates),
            narrative_strength=self._candle_narrative_strength(candidates),
            historical_similarity_count=sum(1 for c in candidates if (c.metadata_json or {}).get("historical_similarity_count")),
            replay_available=bool(candle.evidence_packet_id),
            limitations=SAFETY_LIMITATIONS + ([] if candidates else ["No attribution available."]),
            candidate_events=[self._candidate_event(c, events.get(c.event_id or 0)) for c in candidates if c.event_id],
            candidate_articles=[self._candidate_article(c, articles.get(c.article_id or 0)) for c in candidates if c.article_id],
            candidate_news_events=[self._candidate_event(c, events.get(c.event_id or 0)) for c in candidates if c.event_id],
            candidate_macro_events=[self._candidate_event(c, events.get(c.event_id or 0)) for c in candidates if c.event_id and self._event_is(events.get(c.event_id or 0), "macro")],
            candidate_security_events=[self._candidate_event(c, events.get(c.event_id or 0)) for c in candidates if c.event_id and self._event_is(events.get(c.event_id or 0), "security")],
            candidate_narrative_events=[self._candidate_event(c, events.get(c.event_id or 0)) for c in candidates if c.event_id and not self._event_is(events.get(c.event_id or 0), "security")],
            top_attribution=self._candidate_event(candidates[0], events.get(candidates[0].event_id or 0)) if candidates and candidates[0].event_id else {},
            confidence_breakdown={"attribution_confidence": max([c.normalized_score for c in candidates] or [0.0]), "provider_confidence": candle.provider_confidence, "volatility_score": candle.volatility_score},
            similarity_preview=self.candle_similarity_preview(candle.id, limit=3),
            safety_flags={"correlation_not_causation": True, "evidence_based": True, "operator_reviewed": False, "confidence_score": max([c.normalized_score for c in candidates] or [0.0])},
        )

    def news_markers(self, *, limit: int = 100) -> list[NewsMarkerDTO]:
        rows = list(
            self.db.execute(
                select(NewsEvent)
                .order_by(NewsEvent.first_seen_at.desc(), NewsEvent.id.desc())
                .limit(min(max(limit, 1), 10000))
            ).scalars()
        )
        event_ids = [row.id for row in rows]
        impacts = {
            row.event_id: row
            for row in self.db.execute(
                select(NewsPriceImpact).where(NewsPriceImpact.event_id.in_(event_ids or [0]))
            ).scalars()
            if row.event_id is not None
        }
        evidence = {
            row.event_id: row
            for row in self.db.execute(
                select(EvidencePacket).where(EvidencePacket.event_id.in_(event_ids or [0]))
            ).scalars()
            if row.event_id is not None
        }
        seen: set[tuple[str, str]] = set()
        markers: list[NewsMarkerDTO] = []
        for row in rows:
            marker_type = self._marker_type(row)
            key = (self._dt(row.first_seen_at)[:16], marker_type)
            if key in seen:
                continue
            seen.add(key)
            impact = impacts.get(row.id)
            packet = evidence.get(row.id)
            markers.append(
                NewsMarkerDTO(
                    id=f"event-{row.id}",
                    event_id=row.id,
                    title=row.canonical_title,
                    marker_type=marker_type,
                    marker_style=f"marker-{marker_type.replace('_', '-')}",
                    marker_priority=self._marker_priority(marker_type),
                    timestamp=self._dt(row.first_seen_at),
                    published_at=self._dt(row.first_source_published_at),
                    first_seen=self._dt(row.first_seen_at),
                    confidence=row.event_confidence or row.cluster_confidence or 0.0,
                    evidence_count=max(row.source_count, row.article_count),
                    source=row.first_source_name or "unknown",
                    sentiment=row.event_sentiment,
                    btc_relevance=row.btc_relevance_score,
                    source_confidence=impact.source_credibility_score if impact else 0.0,
                    provider_confidence=impact.provider_confidence if impact else row.provider_confidence,
                    impact_confidence=impact.impact_confidence_score if impact else row.market_impact_score,
                    btc_price_at_publish=impact.price_at_publish if impact else None,
                    change_15m=impact.change_15m_pct if impact else None,
                    change_1h=impact.change_1h_pct if impact else None,
                    change_4h=impact.change_4h_pct if impact else None,
                    change_24h=impact.change_24h_pct if impact else None,
                    evidence_packet_id=packet.id if packet else None,
                    replay_available=packet is not None,
                    similarity_preview=self.event_similarity_preview(row.id, limit=2),
                    limitations=SAFETY_LIMITATIONS,
                )
            )
        return markers

    def event_context(self, event_id: int) -> dict[str, object]:
        event = self.db.get(NewsEvent, event_id)
        if event is None:
            return {"data": None, "limitations": SAFETY_LIMITATIONS + ["Event not found."]}
        marker = next((item for item in self.news_markers(limit=1000) if item.event_id == event_id), None)
        return {
            "data": marker.model_dump() if marker else {
                "event_id": event.id,
                "title": event.canonical_title,
                "first_seen": self._dt(event.first_seen_at),
                "sentiment": event.event_sentiment,
                "btc_relevance": event.btc_relevance_score,
                "provider_confidence": event.provider_confidence,
            },
            "evidence_packet": self._event_evidence_summary(event_id),
            "replay": self.replay_summary("news_event", event_id).model_dump(),
            "similar_historical_events": self.event_similarity_preview(event_id, limit=5),
            "limitations": SAFETY_LIMITATIONS,
        }

    def evidence_panel(self, packet_id: int) -> EvidencePanelDTO:
        packet = self.db.get(EvidencePacket, packet_id)
        if packet is None:
            return EvidencePanelDTO(
                packet_id=packet_id,
                limitations=SAFETY_LIMITATIONS + ["Evidence packet not generated."],
            )
        artifacts = list(
            self.db.execute(
                select(EvidenceArtifact).where(EvidenceArtifact.packet_id == packet_id).order_by(EvidenceArtifact.created_at.asc()).limit(25)
            ).scalars()
        )
        replay_count = self.db.execute(
            select(EvidenceReplayLog).where(
                EvidenceReplayLog.entity_type == packet.source_entity_type,
                EvidenceReplayLog.entity_id == packet.source_entity_id,
            ).limit(1)
        ).scalar_one_or_none()
        return EvidencePanelDTO(
            packet_id=packet.id,
            title=packet.title or f"Evidence packet {packet.id}",
            summary=packet.summary or "Evidence packet summary unavailable.",
            replay_available=replay_count is not None,
            evidence_sources=[{"type": a.artifact_type, "entity_type": a.entity_type, "entity_id": a.entity_id} for a in artifacts],
            provider_confidence=packet.provider_confidence or 0.0,
            source_confidence=packet.source_confidence or 0.0,
            integrity_status="available" if artifacts else "pending",
            operator_review_status="visible" if packet.signal_id else "not_reviewed",
            limitations=SAFETY_LIMITATIONS,
            evidence_summary=packet.summary or "Evidence packet summary unavailable.",
            confidence_breakdown={"packet_confidence": packet.confidence_score or 0.0, "provider_confidence": packet.provider_confidence or 0.0, "source_confidence": packet.source_confidence or 0.0},
            provider_snapshot={"provider_confidence": packet.provider_confidence or 0.0, "degraded_visible": True},
            source_snapshot={"source_confidence": packet.source_confidence or 0.0, "source_entity_type": packet.source_entity_type, "source_entity_id": packet.source_entity_id},
            replay_status="available" if replay_count is not None else "unavailable",
            export_json_url=f"/api/v1/evidence/packets/{packet.id}",
            export_markdown_url=f"/api/v1/evidence/packets/{packet.id}?format=markdown",
            relationships_url=f"/api/v1/evidence/packets/{packet.id}/relationships",
        )

    def replay_summary(self, entity_type: str, entity_id: int) -> ReplaySummaryDTO:
        rows = list(
            self.db.execute(
                select(EvidenceReplayLog)
                .where(EvidenceReplayLog.entity_type == entity_type, EvidenceReplayLog.entity_id == entity_id)
                .order_by(EvidenceReplayLog.started_at.asc(), EvidenceReplayLog.id.asc())
                .limit(50)
            ).scalars()
        )
        return ReplaySummaryDTO(
            entity_type=entity_type,
            entity_id=entity_id,
            replay_available=bool(rows),
            steps=[{"step": r.step_name, "status": "success" if r.success else (r.error_code or "pending"), "created_at": self._dt(r.started_at)} for r in rows],
            limitations=SAFETY_LIMITATIONS + ([] if rows else ["Replay unavailable."]),
        )

    def evidence_for_candle(self, candle_id: int) -> EvidencePanelDTO:
        packet = self.db.execute(
            select(EvidencePacket)
            .where(EvidencePacket.source_entity_type == "btc_candle", EvidencePacket.source_entity_id == candle_id)
            .order_by(EvidencePacket.created_at.desc(), EvidencePacket.id.desc())
            .limit(1)
        ).scalar_one_or_none()
        if packet is not None:
            return self.evidence_panel(packet.id)
        return EvidencePanelDTO(
            title="Evidence packet not generated.",
            summary="No evidence packet generated for this candle.",
            limitations=SAFETY_LIMITATIONS + ["Evidence packet not generated."],
        )

    def event_similarity_preview(self, event_id: int, limit: int = 5) -> list[dict[str, object]]:
        try:
            from app.services.intelligence.historical_similarity_service import HistoricalSimilarityService

            rows = HistoricalSimilarityService(self.db).find_similar_events(
                event_id, limit=min(max(limit, 1), 10), persist_results=False
            )
        except (OperationalError, RuntimeError, ValueError):
            return []
        return [self._similarity_preview(row) for row in rows[:limit]]

    def candle_similarity_preview(self, candle_id: int, limit: int = 5) -> list[dict[str, object]]:
        candidate = self.db.execute(
            select(CandleAttributionCandidate)
            .where(CandleAttributionCandidate.candle_id == candle_id, CandleAttributionCandidate.event_id.is_not(None))
            .order_by(CandleAttributionCandidate.normalized_score.desc(), CandleAttributionCandidate.id.asc())
            .limit(1)
        ).scalar_one_or_none()
        if candidate is None or candidate.event_id is None:
            return []
        return self.event_similarity_preview(candidate.event_id, limit=limit)

    def similarity_panel(self, *, limit: int = 5) -> list[dict[str, object]]:
        row = self.db.execute(
            select(NewsEvent).order_by(NewsEvent.first_seen_at.desc(), NewsEvent.id.desc()).limit(1)
        ).scalar_one_or_none()
        if row is None:
            return []
        return self.event_similarity_preview(row.id, limit=limit)

    def narrative_panel(self, *, limit: int = 9) -> list[dict[str, object]]:
        rows = list(
            self.db.execute(
                select(NarrativeMemorySnapshot)
                .order_by(NarrativeMemorySnapshot.snapshot_time.desc(), NarrativeMemorySnapshot.heat_score.desc())
                .limit(min(max(limit, 1), 25))
            ).scalars()
        )
        if not rows:
            narratives = ["ETF", "Macro", "Fed", "Mining", "Lightning", "Bitcoin Core", "Security", "Institutional Adoption", "Sovereignty"]
            return [
                {
                    "narrative": narrative,
                    "strength": 0.0,
                    "direction": "neutral",
                    "recent_activity": 0,
                    "historical_trend": "insufficient_data",
                }
                for narrative in narratives[:limit]
            ]
        return [
            {
                "narrative": row.narrative,
                "strength": row.heat_score,
                "direction": self._narrative_direction(row),
                "recent_activity": row.event_count,
                "historical_trend": "decaying" if row.decay_score > row.strength_score else "strengthening",
            }
            for row in rows
        ]

    def candle_api_payload(self, candle_id: int) -> dict[str, object]:
        candle = self.candle_attribution(candle_id)
        return {
            "data": candle.model_dump(),
            "timeline_items": self.timeline_for_candle(candle_id),
            "chart_markers": [item.model_dump() for item in self.news_markers(limit=1000) if item.candle_id == candle_id or item.event_id in {event.get("event_id") for event in candle.candidate_events}],
            "evidence_summary": self.evidence_for_candle(candle_id).model_dump(),
            "confidence_breakdown": candle.confidence_breakdown,
            "narrative_strength": candle.narrative_strength,
            "similarity_preview": candle.similarity_preview,
            "operator_status": candle.safety_flags.get("operator_reviewed", False),
            "limitations": candle.limitations,
        }

    def timeline_for_candle(self, candle_id: int, limit: int = 50) -> list[dict[str, object]]:
        rows = list(
            self.db.execute(
                select(IntelligenceTimelineEvent)
                .where(IntelligenceTimelineEvent.related_candle_id == candle_id, IntelligenceTimelineEvent.is_deleted.is_(False))
                .order_by(IntelligenceTimelineEvent.event_time.asc(), IntelligenceTimelineEvent.id.asc())
                .limit(min(max(limit, 1), 100))
            ).scalars()
        )
        return [self._timeline_item(row) for row in rows]

    def timeline_for_event(self, event_id: int, limit: int = 50) -> list[dict[str, object]]:
        rows = list(
            self.db.execute(
                select(IntelligenceTimelineEvent)
                .where(IntelligenceTimelineEvent.related_event_id == event_id, IntelligenceTimelineEvent.is_deleted.is_(False))
                .order_by(IntelligenceTimelineEvent.event_time.asc(), IntelligenceTimelineEvent.id.asc())
                .limit(min(max(limit, 1), 100))
            ).scalars()
        )
        return [self._timeline_item(row) for row in rows]

    def _timeline_item(self, row: IntelligenceTimelineEvent) -> dict[str, object]:
        evidence_refs = row.evidence_refs_json or []
        return {
            "id": row.id,
            "type": row.event_type,
            "title": row.title,
            "summary": row.summary,
            "timestamp": self._dt(row.event_time),
            "confidence": row.confidence_score or 0.0,
            "provider_confidence": row.provider_confidence or 0.0,
            "evidence_count": len(evidence_refs),
            "status": "replayed" if row.is_replayed else row.visibility.lower(),
            "related_candle_id": row.related_candle_id,
            "related_event_id": row.related_event_id,
            "related_signal_id": row.related_signal_id,
            "limitations": row.limitations_json or SAFETY_LIMITATIONS,
        }

    def _normalize_filters(self, raw_filters: list[str] | str) -> list[str]:
        if isinstance(raw_filters, str):
            parts = [part.strip().lower() for part in raw_filters.split(",")]
        else:
            parts = [part.strip().lower() for part in raw_filters]
        normalized: list[str] = []
        aliases = {"institutional": "institutional", "etf": "institutional", "high confidence only": "high_confidence", "operator reviewed only": "operator_reviewed"}
        for part in parts:
            value = aliases.get(part, part)
            if value in FILTERS and value not in normalized:
                normalized.append(value)
        return normalized or ["all"]

    def _apply_filter(self, query: Any, filter_name: str) -> Any:
        if filter_name == "news":
            return query.where(IntelligenceTimelineEvent.related_event_id.is_not(None))
        if filter_name == "candles":
            return query.where(IntelligenceTimelineEvent.related_candle_id.is_not(None))
        if filter_name == "signals":
            return query.where(IntelligenceTimelineEvent.related_signal_id.is_not(None))
        if filter_name == "high_confidence":
            return query.where(IntelligenceTimelineEvent.confidence_score >= 0.75)
        if filter_name == "operator_reviewed":
            return query.where(IntelligenceTimelineEvent.event_type.in_(["operator_review", "publication"]))
        if filter_name == "operator_actions":
            return query.where(IntelligenceTimelineEvent.event_type.in_(["operator_review", "publication", "operator_action"]))
        return query.where(IntelligenceTimelineEvent.tags_json.contains([filter_name]))

    def _apply_window(self, query: Any, window: str) -> Any:
        windows = {"1h": timedelta(hours=1), "4h": timedelta(hours=4), "24h": timedelta(hours=24), "7d": timedelta(days=7), "30d": timedelta(days=30)}
        if window in windows:
            return query.where(IntelligenceTimelineEvent.event_time >= datetime.utcnow() - windows[window])
        return query



    @staticmethod
    def _float_value(value: object) -> float:
        return float(value) if isinstance(value, int | float | str) else 0.0

    @staticmethod
    def _int_value(value: object) -> int:
        return int(value) if isinstance(value, int | float | str) else 0

    def _signal_bucket(self, row: IntelligenceSignalCandidate) -> str:
        text = f"{row.status} {row.policy_decision} {row.policy_reason}".lower()
        if row.published_at is not None or "published" in text:
            return "published"
        if "false" in text:
            return "false_positive"
        if "reject" in text:
            return "rejected"
        if "expire" in text:
            return "expired"
        if "hold" in text or "held" in text:
            return "held"
        if row.requires_operator_review or "review" in text or "pending" in text:
            return "pending_review"
        return row.status or "pending_review"

    def _candidate_event(self, candidate: CandleAttributionCandidate, event: NewsEvent | None) -> dict[str, object]:
        return {
            "event_id": candidate.event_id,
            "title": event.canonical_title if event else "Candidate event",
            "confidence": candidate.normalized_score,
            "time_distance_seconds": candidate.time_distance_seconds,
            "direction_match": candidate.direction_match_score,
            "evidence_count": event.article_count if event else 0,
        }

    def _candidate_article(self, candidate: CandleAttributionCandidate, article: NewsArticle | None) -> dict[str, object]:
        return {
            "article_id": candidate.article_id,
            "title": article.title if article else "Candidate article",
            "confidence": candidate.normalized_score,
            "time_distance_seconds": candidate.time_distance_seconds,
            "source": f"source:{article.source_id}" if article else "unknown",
        }

    def _marker_type(self, event: NewsEvent) -> str:
        text = f"{event.canonical_title} {event.event_type} {event.event_category}".lower()
        if event.is_security_related or "hack" in text or "security" in text:
            return "security"
        if event.is_regulatory_related or "sec" in text or "regulat" in text:
            return "regulatory"
        if event.is_institutional_related or "etf" in text or "institution" in text:
            return "institutional"
        if "mining" in text or "miner" in text:
            return "mining"
        if "lightning" in text or "bitcoin core" in text:
            return "lightning"
        sentiment = (event.event_sentiment or "").lower()
        if sentiment == "positive":
            return "positive"
        if sentiment == "negative":
            return "negative"
        return "uncertain"

    def _marker_priority(self, marker_type: str) -> int:
        return {"security": 1, "regulatory": 2, "institutional": 3, "positive": 4, "negative": 4, "mining": 5, "lightning": 5, "uncertain": 8}.get(marker_type, 9)

    def _event_evidence_summary(self, event_id: int) -> dict[str, object]:
        packet = self.db.execute(
            select(EvidencePacket)
            .where(EvidencePacket.event_id == event_id)
            .order_by(EvidencePacket.created_at.desc(), EvidencePacket.id.desc())
            .limit(1)
        ).scalar_one_or_none()
        if packet is None:
            return {"available": False, "summary": "Evidence packet not generated."}
        return {"available": True, "packet_id": packet.id, "summary": packet.summary}

    def _similarity_preview(self, row: dict[str, object]) -> dict[str, object]:
        similar_event = row.get("candidate_event") or row.get("similar_event") or {}
        if not isinstance(similar_event, dict):
            similar_event = {}
        reaction = row.get("reaction") if isinstance(row.get("reaction"), dict) else {}
        pattern = row.get("matched_pattern") or row.get("pattern") or row.get("pattern_code") or "unknown"
        return {
            "similar_event": similar_event.get("title") or row.get("title") or "Historical event",
            "date": similar_event.get("first_seen_at") or row.get("date") or row.get("created_at") or "unknown",
            "pattern": pattern,
            "reaction": reaction or row.get("historical_reaction") or "historical_reference_only",
            "confidence": row.get("confidence_score") or row.get("similarity_score") or row.get("overall_confidence") or 0.0,
            "median_historical_move": row.get("median_historical_move") or 0.0,
            "typical_window": row.get("typical_window") or "unknown",
            "pattern_reliability": row.get("pattern_reliability") or row.get("provider_confidence") or 0.0,
        }

    def _narrative_direction(self, row: NarrativeMemorySnapshot) -> str:
        if row.market_reaction > 0.05:
            return "positive"
        if row.market_reaction < -0.05:
            return "negative"
        return "neutral"

    def _dominant_direction(self, open_value: float | None, close_value: float | None) -> str:
        change = self._price_change(open_value, close_value)
        if change > 0.05:
            return "up"
        if change < -0.05:
            return "down"
        return "neutral"

    def _candle_narrative_strength(self, candidates: list[CandleAttributionCandidate]) -> float:
        strengths: list[float] = []
        for candidate in candidates:
            raw_value = (candidate.metadata_json or {}).get("narrative_strength", 0.0)
            if isinstance(raw_value, int | float | str):
                strengths.append(float(raw_value))
        return max(strengths or [0.0])

    def _event_is(self, event: NewsEvent | None, category: str) -> bool:
        if event is None:
            return False
        text = f"{event.event_type} {event.event_category} {event.canonical_title}".lower()
        if category == "macro":
            return event.is_macro_related or "macro" in text or "fed" in text or "cpi" in text
        if category == "security":
            return event.is_security_related or "security" in text or "hack" in text
        return category in text

    def _price_change(self, open_value: float | None, close_value: float | None) -> float:
        if not open_value or close_value is None:
            return 0.0
        return round(((close_value - open_value) / open_value) * 100, 4)

    def _dt(self, value: datetime | None) -> str:
        return value.isoformat() if value else "unknown"


def safe_dashboard(db: Session, timeframe: str = "1h", page_size: int = 80) -> MarketTimelineDTO:
    try:
        return MarketTimeMachineWebService(db).dashboard(timeframe=timeframe, page_size=page_size)
    except OperationalError:
        return MarketTimelineDTO(limitations=SAFETY_LIMITATIONS + ["Data temporarily unavailable."])
