"""Typed projections over authoritative historical Market persistence."""

from __future__ import annotations

import hashlib
import json
from uuid import UUID, uuid5

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models.candle_attribution import CandleAttribution
from app.db.models.evidence_packet import EvidenceIntegritySnapshot, EvidencePacket
from app.db.models.intelligence_timeline import IntelligenceTimelineEvent
from app.db.models.market_narrative import MarketNarrative
from app.db.models.news_source import NewsSource
from app.schemas.market_history import (
    AttributionRelation,
    BrowserSafeMarketSourceOut,
    MarketAttributionOut,
    MarketEvidenceLink,
    MarketEvidenceRelation,
    MarketNarrativeOut,
    MarketReplayCaptureOut,
    MarketSourceRef,
    MarketSourceType,
    MarketTimelineEventOut,
    MarketTimelinePageOut,
    NarrativeOrigin,
    ReplayIntegrityOut,
    TimelineKind,
)

CAPTURE_NAMESPACE = UUID("9da28d15-21df-4b37-849d-2deaa3aa9ad5")


def _kind(value: str) -> TimelineKind:
    normalized = value.casefold()
    for needle, kind in (
        ("narrative", TimelineKind.NARRATIVE),
        ("signal", TimelineKind.SIGNAL),
        ("provider", TimelineKind.PROVIDER),
        ("news", TimelineKind.NEWS),
        ("market", TimelineKind.MARKET),
    ):
        if needle in normalized:
            return kind
    return TimelineKind.OTHER


def _source(value: str) -> MarketSourceRef:
    normalized = value.casefold()
    source_type = {
        "news": MarketSourceType.NEWS,
        "signal": MarketSourceType.SIGNAL,
        "provider": MarketSourceType.PROVIDER,
        "market": MarketSourceType.MARKET_DATA,
        "internal": MarketSourceType.INTERNAL,
    }.get(normalized, MarketSourceType.UNKNOWN)
    return MarketSourceRef(
        source_id=f"timeline:{normalized}", display_name=value, source_type=source_type
    )


class MarketHistoryService:
    """Default-deny browser projection; raw JSON fields never cross this boundary."""

    def __init__(self, db: Session):
        self.db = db

    def _evidence(
        self, *, event_id: int | None = None, attribution_id: int | None = None
    ) -> tuple[MarketEvidenceLink, ...]:
        query = self.db.query(EvidencePacket)
        conditions = []
        if event_id is not None:
            conditions.append(EvidencePacket.event_id == event_id)
        if attribution_id is not None:
            conditions.append(EvidencePacket.attribution_id == attribution_id)
        if not conditions:
            return ()
        packets = query.filter(or_(*conditions)).order_by(EvidencePacket.id).limit(20).all()
        links = []
        for packet in packets:
            integrity = (
                self.db.query(EvidenceIntegritySnapshot.id)
                .filter(
                    EvidenceIntegritySnapshot.entity_type == "evidence_packet",
                    EvidenceIntegritySnapshot.entity_id == packet.id,
                )
                .first()
            )
            links.append(
                MarketEvidenceLink(
                    evidence_id=packet.id,
                    relation=MarketEvidenceRelation.RELATED_EVIDENCE,
                    label=packet.title or f"Evidence {packet.id}",
                    linked_at=packet.created_at,
                    verification_status="INTEGRITY_RECORD_AVAILABLE"
                    if integrity
                    else "NOT_REQUESTED",
                )
            )
        return tuple(links)

    def event(self, row: IntelligenceTimelineEvent) -> MarketTimelineEventOut:
        return MarketTimelineEventOut(
            event_id=row.id,
            sequence=row.id,
            kind=_kind(row.event_type),
            producer_type=row.event_type,
            occurred_at=row.event_time,
            observed_at=row.ingested_at,
            source=_source(row.source_kind),
            title=row.title,
            summary=row.summary,
            related_signal_id=row.related_signal_id,
            related_candle_id=row.related_candle_id,
            evidence_links=self._evidence(event_id=row.related_event_id),
            limitations=tuple(row.limitations_json or ()),
        )

    def timeline(self, *, limit: int, before_sequence: int | None = None) -> MarketTimelinePageOut:
        query = self.db.query(IntelligenceTimelineEvent).filter(
            IntelligenceTimelineEvent.is_deleted.is_(False)
        )
        if before_sequence is not None:
            query = query.filter(IntelligenceTimelineEvent.id < before_sequence)
        rows = (
            query.order_by(
                IntelligenceTimelineEvent.event_time.desc(), IntelligenceTimelineEvent.id.desc()
            )
            .limit(limit + 1)
            .all()
        )
        page, has_more = rows[:limit], len(rows) > limit
        return MarketTimelinePageOut(
            items=tuple(self.event(row) for row in page),
            limit=limit,
            next_before_sequence=page[-1].id if has_more and page else None,
        )

    @staticmethod
    def _capture_payload(event: MarketTimelineEventOut) -> bytes:
        return json.dumps(
            event.model_dump(mode="json"), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()

    def capture_for_event(self, event_id: int) -> MarketReplayCaptureOut | None:
        row = self.db.get(IntelligenceTimelineEvent, event_id)
        if row is None or row.is_deleted:
            return None
        event = self.event(row)
        digest = hashlib.sha256(self._capture_payload(event)).hexdigest()
        return MarketReplayCaptureOut(
            capture_id=uuid5(CAPTURE_NAMESPACE, digest),
            captured_at=row.updated_at,
            effective_at=row.event_time,
            event=event,
            integrity=ReplayIntegrityOut(content_digest=digest),
            limitations=("Content digest proves equality, not external truth or causality.",),
        )

    def attributions(self, limit: int) -> tuple[MarketAttributionOut, ...]:
        rows = (
            self.db.query(CandleAttribution)
            .order_by(CandleAttribution.id.desc())
            .limit(limit)
            .all()
        )
        result = []
        for row in rows:
            relation = (
                AttributionRelation.CORRELATION_CANDIDATE
                if row.attribution_type == "correlation_candidate"
                else AttributionRelation.ASSOCIATED
            )
            result.append(
                MarketAttributionOut(
                    attribution_id=row.id,
                    subject_candle_id=row.candle_id,
                    factor_event_id=row.event_id,
                    relation=relation,
                    confidence_ratio=max(0.0, min(1.0, row.confidence_score)),
                    explanation=(row.summary_text or "Backend-associated candidate."),
                    limitations=tuple(
                        str(value) for value in (row.limitations_json or {}).values()
                    ),
                    evidence_links=self._evidence(attribution_id=row.id),
                )
            )
        return tuple(result)

    def narratives(self, limit: int) -> tuple[MarketNarrativeOut, ...]:
        rows = (
            self.db.query(MarketNarrative)
            .order_by(MarketNarrative.updated_at.desc())
            .limit(limit)
            .all()
        )
        return tuple(
            MarketNarrativeOut(
                narrative_id=row.id,
                slug=row.slug,
                title=row.display_name or row.name,
                body_plain_text=row.description,
                origin=NarrativeOrigin.STORED_BACKEND_RECORD,
                generated_at=row.updated_at,
                confidence_ratio=max(0.0, min(1.0, row.avg_confidence)),
                limitations=("Stored analytical narrative; not a causal finding.",),
            )
            for row in rows
        )

    def sources(self, limit: int) -> tuple[BrowserSafeMarketSourceOut, ...]:
        rows = (
            self.db.query(NewsSource)
            .filter(NewsSource.is_public.is_(True))
            .order_by(NewsSource.id)
            .limit(limit)
            .all()
        )
        result = []
        for row in rows:
            url = row.homepage_url or None
            try:
                result.append(
                    BrowserSafeMarketSourceOut(
                        source_id=row.uuid,
                        display_name=row.name,
                        source_type=MarketSourceType.NEWS,
                        category=row.category,
                        homepage_url=url,
                        observed_at=row.last_success_at,
                        limitations=(("Source is currently degraded.",) if row.is_degraded else ()),
                    )
                )
            except ValueError:
                result.append(
                    BrowserSafeMarketSourceOut(
                        source_id=row.uuid,
                        display_name=row.name,
                        source_type=MarketSourceType.NEWS,
                        category=row.category,
                        homepage_url=None,
                        observed_at=row.last_success_at,
                        limitations=("Configured source URL is not browser-safe.",),
                    )
                )
        return tuple(result)
