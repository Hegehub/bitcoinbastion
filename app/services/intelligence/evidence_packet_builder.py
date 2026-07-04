from __future__ import annotations

import json
from datetime import datetime
from hashlib import sha256
from typing import Any, cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.candle_attribution import CandleAttribution
from app.db.models.evidence_packet import (
    EvidenceArtifact,
    EvidenceIntegritySnapshot,
    EvidencePacket,
    EvidenceRelationship,
)
from app.db.models.intelligence_signals import (
    IntelligenceOperatorReview,
    IntelligenceSignalCandidate,
)
from app.db.models.news_article import NewsArticle
from app.db.models.news_event import NewsEvent
from app.db.models.news_price_impact import NewsPriceImpact
from app.repositories.evidence_repository import EvidenceRepository
from app.services.events.domain_event_publisher import publish_domain_event
from app.services.intelligence.evidence_metrics import EVIDENCE_PACKETS_GENERATED_TOTAL

SECRET_KEY_PARTS = ("secret", "token", "password", "api_key", "apikey", "private_key")
ENTITY_ALIASES = {
    "news_article": "article",
    "article": "article",
    "news_event": "event",
    "event": "event",
    "news_price_impact": "impact",
    "impact": "impact",
    "candle_attribution": "attribution",
    "attribution": "attribution",
    "intelligence_signal_candidate": "signal",
    "signal": "signal",
    "publication": "publication",
}


class EvidencePacketBuilder:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = EvidenceRepository(db)

    def build(self, entity_type: str, entity_id: int) -> EvidencePacket:
        normalized = self.normalize_entity_type(entity_type)
        entity = self.load_entity(normalized, entity_id)
        if entity is None:
            raise ValueError("evidence_entity_not_found")
        packet = EvidencePacket(
            packet_type=f"{normalized}_evidence",
            source_entity_type=normalized,
            source_entity_id=entity_id,
            article_id=self._article_id(normalized, entity),
            event_id=self._event_id(normalized, entity),
            impact_id=entity.id if normalized == "impact" else self._impact_id(normalized, entity),
            attribution_id=(
                entity.id
                if normalized == "attribution"
                else self._attribution_id(normalized, entity)
            ),
            signal_id=entity.id if normalized == "signal" else None,
            title=self._title(normalized, entity),
            summary=self._summary(normalized, entity),
            confidence_score=self._confidence(normalized, entity),
            provider_confidence=getattr(entity, "provider_confidence", None),
            source_confidence=self._source_confidence(normalized, entity),
        )
        self.repo.add_packet(packet)
        self._build_relationships(normalized, entity)
        integrity = self.create_integrity_snapshot(normalized, entity_id)
        payload = self.packet_payload(packet, integrity_snapshot=integrity)
        for artifact_type in [
            "evidence_summary",
            "evidence_sources",
            "confidence_breakdown",
            "provider_health_snapshot",
            "source_health_snapshot",
            "replay_references",
            "limitations",
            "frontend_dto",
        ]:
            self.repo.add_artifact(
                EvidenceArtifact(
                    packet_id=packet.id,
                    entity_type=normalized,
                    entity_id=entity_id,
                    artifact_type=artifact_type,
                    artifact_json={
                        artifact_type: payload.get(artifact_type)
                        or payload.get(self._payload_key(artifact_type), {})
                    },
                )
            )
        EVIDENCE_PACKETS_GENERATED_TOTAL.labels(
            packet_type=self._bounded_packet_type(packet.packet_type)
        ).inc()
        publish_domain_event(
            self.db,
            "evidence.packet.created",
            {
                "packet_id": packet.id,
                "source_entity_type": packet.source_entity_type,
                "source_entity_id": packet.source_entity_id,
                "integrity_hash": integrity.content_hash if integrity else None,
                "confidence": packet.confidence_score,
                "limitations": self.limitations(packet, entity),
                "operator_reviewed": self._operator_review_status(packet.signal_id) != "none",
                "publication_status": self._publication_status(packet.signal_id),
                "evidence_based": True,
                "replayable": True,
            },
            aggregate_type="evidence_packet",
            aggregate_id=packet.id,
            source="evidence_packet_builder",
            idempotency_key=f"evidence.packet.created:evidence_packet:{packet.id}:created",
        )
        return packet

    def packet_payload(
        self, packet: EvidencePacket, *, integrity_snapshot: EvidenceIntegritySnapshot | None = None
    ) -> dict[str, Any]:
        entity = self.load_entity(packet.source_entity_type, packet.source_entity_id)
        relationships = self.relationship_chain(packet.source_entity_type, packet.source_entity_id)
        artifacts = self.repo.artifacts_for_packet(packet.id) if packet.id else []
        integrity = integrity_snapshot or self.repo.latest_integrity_snapshot(
            packet.source_entity_type, packet.source_entity_id
        )
        return {
            "packet_id": packet.id,
            "packet_type": packet.packet_type,
            "source_entity_type": packet.source_entity_type,
            "source_entity_id": packet.source_entity_id,
            "title": packet.title,
            "summary": packet.summary,
            "evidence_summary": {
                "title": packet.title,
                "summary": packet.summary,
                "confidence_score": packet.confidence_score,
                "correlation_not_causation": True,
                "evidence_based": True,
                "replayable": True,
                "operator_reviewed": self._operator_review_status(packet.signal_id) != "none",
            },
            "evidence_sources": self._evidence_sources(packet),
            "confidence_breakdown": self.confidence_breakdown(packet, entity),
            "provider_health_snapshot": self.provider_health_snapshot(packet, entity),
            "source_health_snapshot": self.source_health_snapshot(packet, entity),
            "replay_references": self.replay_references(packet),
            "limitations": self.limitations(packet, entity),
            "integrity_snapshot": self.integrity_payload(integrity),
            "timeline": self.timeline_for(packet.source_entity_type, packet.source_entity_id),
            "evidence_chain": [self.relationship_payload(row) for row in relationships],
            "relationships": [self.relationship_payload(row) for row in relationships],
            "artifacts": [self.artifact_payload(row) for row in artifacts],
            "integrity_status": "snapshot_available" if integrity else "missing_snapshot",
            "operator_review_status": self._operator_review_status(packet.signal_id),
            "publication_status": self._publication_status(packet.signal_id),
            "correlation_not_causation": True,
            "evidence_based": True,
            "replayable": True,
            "operator_reviewed": self._operator_review_status(packet.signal_id) != "none",
        }

    def create_integrity_snapshot(
        self, entity_type: str, entity_id: int
    ) -> EvidenceIntegritySnapshot:
        normalized = self.normalize_entity_type(entity_type)
        content_hash = self.entity_hash(normalized, entity_id)
        return self.repo.add_integrity_snapshot(
            EvidenceIntegritySnapshot(
                entity_type=normalized,
                entity_id=entity_id,
                hash_algorithm="sha256",
                content_hash=content_hash,
            )
        )

    def entity_hash(self, entity_type: str, entity_id: int) -> str:
        normalized = self.normalize_entity_type(entity_type)
        entity = self.load_entity(normalized, entity_id)
        if entity is None:
            raise ValueError("evidence_entity_not_found")
        payload = self.entity_public_payload(normalized, entity)
        encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode(
            "utf-8"
        )
        return sha256(encoded).hexdigest()

    def entity_public_payload(self, entity_type: str, entity: Any) -> dict[str, Any]:
        fields = {
            "article": [
                "id",
                "source_id",
                "title",
                "summary",
                "published_at",
                "fetched_at",
                "provider_confidence",
                "btc_relevance_score",
                "market_impact_score",
                "credibility_score",
                "confidence_score",
                "content_hash",
            ],
            "event": [
                "id",
                "primary_article_id",
                "canonical_title",
                "canonical_summary",
                "event_type",
                "event_category",
                "event_confidence",
                "provider_confidence",
                "btc_relevance_score",
                "market_impact_score",
                "source_count",
                "first_seen_at",
                "last_seen_at",
            ],
            "impact": [
                "id",
                "article_id",
                "event_id",
                "impact_confidence_score",
                "confidence_score",
                "provider_confidence",
                "source_credibility_score",
                "btc_relevance_score",
                "market_impact_score",
                "dominant_window",
                "delayed_reaction_detected",
                "false_signal_detected",
                "calculated_at",
            ],
            "attribution": [
                "id",
                "article_id",
                "event_id",
                "candle_id",
                "confidence_score",
                "provider_confidence",
                "source_confidence",
                "btc_relevance_score",
                "market_impact_score",
                "price_move_pct",
                "dominant_window",
                "created_at",
            ],
            "signal": [
                "id",
                "signal_type",
                "source_entity_type",
                "source_entity_id",
                "article_id",
                "event_id",
                "impact_id",
                "attribution_id",
                "title",
                "summary",
                "confidence_score",
                "provider_confidence",
                "source_confidence",
                "policy_decision",
                "policy_reason",
                "status",
                "requires_operator_review",
                "published_at",
                "created_at",
            ],
            "publication": [
                "id",
                "signal_type",
                "status",
                "published_at",
                "policy_decision",
                "policy_reason",
            ],
        }[entity_type]
        return cast(
            dict[str, Any],
            self._sanitize({field: getattr(entity, field, None) for field in fields}),
        )

    def confidence_breakdown(
        self, packet: EvidencePacket, entity: Any | None = None
    ) -> dict[str, Any]:
        return {
            "source_contribution": packet.source_confidence,
            "provider_contribution": packet.provider_confidence,
            "impact_contribution": getattr(entity, "impact_confidence_score", None)
            or getattr(entity, "market_impact_score", None),
            "attribution_contribution": (
                getattr(entity, "confidence_score", None) if packet.attribution_id else None
            ),
            "policy_adjustments": getattr(entity, "policy_reason", None),
            "operator_overrides": self._operator_overrides(packet.signal_id),
            "final_confidence": packet.confidence_score,
        }

    def provider_health_snapshot(
        self, packet: EvidencePacket, entity: Any | None = None
    ) -> dict[str, Any]:
        confidence = packet.provider_confidence
        return {
            "provider_confidence": confidence,
            "provider_degraded": confidence is not None and confidence < 0.6,
        }

    def source_health_snapshot(
        self, packet: EvidencePacket, entity: Any | None = None
    ) -> dict[str, Any]:
        confidence = packet.source_confidence
        return {
            "source_confidence": confidence,
            "low_source_diversity": self._low_source_diversity(packet, entity),
        }

    def replay_references(self, packet: EvidencePacket) -> dict[str, Any]:
        refs = {
            "entity": f"{packet.source_entity_type}:{packet.source_entity_id}",
            "replay_endpoint": f"/api/v1/evidence/replay/{packet.source_entity_type}/{packet.source_entity_id}",
        }
        if packet.attribution_id:
            refs["attribution_replay"] = f"candle_attribution:{packet.attribution_id}"
        return refs

    def limitations(self, packet: EvidencePacket, entity: Any | None = None) -> dict[str, bool]:
        confidence = packet.provider_confidence
        return {
            "correlation_not_causation": True,
            "provider_degraded": confidence is not None and confidence < 0.6,
            "low_source_diversity": self._low_source_diversity(packet, entity),
            "limited_market_data": packet.impact_id is None and packet.attribution_id is None,
            "operator_override_used": bool(self._operator_overrides(packet.signal_id)),
            "missing_external_confirmation": packet.event_id is None,
            "historical_similarity_unavailable": True,
            "evidence_based": True,
            "replayable": True,
            "operator_reviewed": self._operator_review_status(packet.signal_id) != "none",
        }

    def timeline_for(self, entity_type: str, entity_id: int) -> list[dict[str, Any]]:
        normalized = self.normalize_entity_type(entity_type)
        entities = self.related_entities(normalized, entity_id)
        steps: list[dict[str, Any]] = []
        article = entities.get("article")
        event = entities.get("event")
        impact = entities.get("impact")
        attribution = entities.get("attribution")
        signal = entities.get("signal")
        if article:
            steps.append(
                self._timeline_step(
                    "article_fetched",
                    article.id,
                    getattr(article, "fetched_at", None),
                    "Article fetched",
                )
            )
        if event:
            steps.append(
                self._timeline_step(
                    "event_clustered",
                    event.id,
                    getattr(event, "first_seen_at", None),
                    "Event clustered",
                )
            )
        if impact:
            steps.append(
                self._timeline_step(
                    "impact_calculated",
                    impact.id,
                    getattr(impact, "calculated_at", None),
                    "Impact calculated",
                )
            )
        if attribution:
            steps.append(
                self._timeline_step(
                    "attribution_created",
                    attribution.id,
                    getattr(attribution, "created_at", None),
                    "Attribution created",
                )
            )
        if signal:
            steps.append(
                self._timeline_step(
                    "signal_candidate_created",
                    signal.id,
                    getattr(signal, "created_at", None),
                    "Signal candidate created",
                )
            )
            steps.append(
                self._timeline_step(
                    "policy_evaluated",
                    signal.id,
                    getattr(signal, "updated_at", None),
                    "Policy evaluated",
                )
            )
            review = self._latest_review(signal.id)
            if review:
                steps.append(
                    self._timeline_step(
                        "operator_reviewed", review.id, review.created_at, "Operator reviewed"
                    )
                )
            if signal.published_at:
                steps.append(
                    self._timeline_step("published", signal.id, signal.published_at, "Published")
                )
        return steps

    def related_entities(self, entity_type: str, entity_id: int) -> dict[str, Any]:
        normalized = self.normalize_entity_type(entity_type)
        entity = self.load_entity(normalized, entity_id)
        result: dict[str, Any] = {normalized: entity} if entity is not None else {}
        if entity is None:
            return result
        signal = entity if normalized == "signal" else self._find_signal(normalized, entity)
        attribution = (
            entity
            if normalized == "attribution"
            else self._find_attribution(normalized, entity, signal)
        )
        impact = entity if normalized == "impact" else self._find_impact(normalized, entity, signal)
        event = (
            entity
            if normalized == "event"
            else self._find_event(normalized, entity, signal, attribution, impact)
        )
        article = (
            entity
            if normalized == "article"
            else self._find_article(normalized, entity, signal, attribution, impact, event)
        )
        for key, value in [
            ("article", article),
            ("event", event),
            ("impact", impact),
            ("attribution", attribution),
            ("signal", signal),
        ]:
            if value is not None:
                result[key] = value
        return result

    def load_entity(self, entity_type: str, entity_id: int) -> Any | None:
        normalized = self.normalize_entity_type(entity_type)
        model = {
            "article": NewsArticle,
            "event": NewsEvent,
            "impact": NewsPriceImpact,
            "attribution": CandleAttribution,
            "signal": IntelligenceSignalCandidate,
            "publication": IntelligenceSignalCandidate,
        }[normalized]
        return self.db.get(model, entity_id)

    def normalize_entity_type(self, entity_type: str) -> str:
        normalized = ENTITY_ALIASES.get(entity_type.lower())
        if normalized is None:
            raise ValueError("unsupported_evidence_entity_type")
        return normalized

    def relationship_chain(self, entity_type: str, entity_id: int) -> list[EvidenceRelationship]:
        entities = self.related_entities(entity_type, entity_id)
        seen: dict[int, EvidenceRelationship] = {}
        for key, entity in entities.items():
            for row in self.repo.relationships_for_entity(key, entity.id):
                seen[row.id] = row
        return sorted(seen.values(), key=lambda row: (row.created_at, row.id))

    def relationship_payload(self, row: EvidenceRelationship) -> dict[str, Any]:
        return {
            "id": row.id,
            "parent_entity_type": row.parent_entity_type,
            "parent_entity_id": row.parent_entity_id,
            "child_entity_type": row.child_entity_type,
            "child_entity_id": row.child_entity_id,
            "relationship_type": row.relationship_type,
            "created_at": row.created_at,
        }

    def artifact_payload(self, row: EvidenceArtifact) -> dict[str, Any]:
        return {
            "id": row.id,
            "artifact_type": row.artifact_type,
            "artifact_json": row.artifact_json,
            "created_at": row.created_at,
        }

    def integrity_payload(self, row: EvidenceIntegritySnapshot | None) -> dict[str, Any] | None:
        if row is None:
            return None
        return {
            "id": row.id,
            "entity_type": row.entity_type,
            "entity_id": row.entity_id,
            "hash_algorithm": row.hash_algorithm,
            "content_hash": row.content_hash,
            "created_at": row.created_at,
        }

    def export_packet(self, packet: EvidencePacket, *, fmt: str = "json") -> dict[str, Any] | str:
        payload = self.packet_payload(packet)
        if fmt == "json":
            return payload
        if fmt != "markdown":
            raise ValueError("unsupported_export_format")
        limitations = payload["limitations"]
        limitation_lines = "\n".join(f"- {key}: {value}" for key, value in limitations.items())
        return (
            f"# Evidence Packet {packet.id}\n\n"
            f"## Summary\n{packet.title}\n\n{packet.summary}\n\n"
            f"## Confidence\n{json.dumps(payload['confidence_breakdown'], default=str, sort_keys=True)}\n\n"
            f"## Limitations\n{limitation_lines}\n\n"
            "Correlation-based attribution is not proof of causation. Not financial advice."
        )

    def _build_relationships(self, entity_type: str, entity: Any) -> None:
        entities = self.related_entities(entity_type, entity.id)
        chain = [
            ("article", "event", "article_to_news_event"),
            ("event", "impact", "news_event_to_price_impact"),
            ("impact", "attribution", "price_impact_to_attribution"),
            ("attribution", "signal", "attribution_to_signal"),
            ("signal", "publication", "signal_to_publication"),
        ]
        for parent_key, child_key, rel_type in chain:
            parent = entities.get(parent_key)
            child = entities.get(child_key)
            if parent is None or child is None:
                continue
            if child_key == "publication" and getattr(child, "published_at", None) is None:
                continue
            self.repo.add_relationship(
                EvidenceRelationship(
                    parent_entity_type=parent_key,
                    parent_entity_id=parent.id,
                    child_entity_type=child_key,
                    child_entity_id=child.id,
                    relationship_type=rel_type,
                )
            )

    def _find_signal(self, entity_type: str, entity: Any) -> IntelligenceSignalCandidate | None:
        if entity_type == "signal":
            return cast(IntelligenceSignalCandidate, entity)
        filters = []
        if entity_type == "article":
            filters.append(IntelligenceSignalCandidate.article_id == entity.id)
        if entity_type == "event":
            filters.append(IntelligenceSignalCandidate.event_id == entity.id)
        if entity_type == "impact":
            filters.append(IntelligenceSignalCandidate.impact_id == entity.id)
        if entity_type == "attribution":
            filters.append(IntelligenceSignalCandidate.attribution_id == entity.id)
        if not filters:
            return None
        return self.db.execute(
            select(IntelligenceSignalCandidate)
            .where(*filters)
            .order_by(IntelligenceSignalCandidate.id.desc())
            .limit(1)
        ).scalar_one_or_none()

    def _find_attribution(
        self, entity_type: str, entity: Any, signal: IntelligenceSignalCandidate | None
    ) -> CandleAttribution | None:
        if signal and signal.attribution_id:
            return self.db.get(CandleAttribution, signal.attribution_id)
        if entity_type == "impact":
            return self.db.execute(
                select(CandleAttribution)
                .where(CandleAttribution.event_id == entity.event_id)
                .limit(1)
            ).scalar_one_or_none()
        if entity_type == "event":
            return self.db.execute(
                select(CandleAttribution).where(CandleAttribution.event_id == entity.id).limit(1)
            ).scalar_one_or_none()
        return None

    def _find_impact(
        self, entity_type: str, entity: Any, signal: IntelligenceSignalCandidate | None
    ) -> NewsPriceImpact | None:
        if signal and signal.impact_id:
            return self.db.get(NewsPriceImpact, signal.impact_id)
        if entity_type == "attribution":
            return self.db.execute(
                select(NewsPriceImpact).where(NewsPriceImpact.event_id == entity.event_id).limit(1)
            ).scalar_one_or_none()
        if entity_type == "event":
            return self.db.execute(
                select(NewsPriceImpact).where(NewsPriceImpact.event_id == entity.id).limit(1)
            ).scalar_one_or_none()
        if entity_type == "article":
            return self.db.execute(
                select(NewsPriceImpact).where(NewsPriceImpact.article_id == entity.id).limit(1)
            ).scalar_one_or_none()
        return None

    def _find_event(
        self,
        entity_type: str,
        entity: Any,
        signal: IntelligenceSignalCandidate | None,
        attribution: CandleAttribution | None,
        impact: NewsPriceImpact | None,
    ) -> NewsEvent | None:
        event_id = (
            getattr(signal, "event_id", None)
            or getattr(attribution, "event_id", None)
            or getattr(impact, "event_id", None)
        )
        if event_id:
            return self.db.get(NewsEvent, event_id)
        if entity_type == "article":
            return self.db.execute(
                select(NewsEvent).where(NewsEvent.primary_article_id == entity.id).limit(1)
            ).scalar_one_or_none()
        return None

    def _find_article(
        self,
        entity_type: str,
        entity: Any,
        signal: IntelligenceSignalCandidate | None,
        attribution: CandleAttribution | None,
        impact: NewsPriceImpact | None,
        event: NewsEvent | None,
    ) -> NewsArticle | None:
        article_id = (
            getattr(signal, "article_id", None)
            or getattr(attribution, "article_id", None)
            or getattr(impact, "article_id", None)
            or getattr(event, "primary_article_id", None)
        )
        if article_id:
            return self.db.get(NewsArticle, article_id)
        return None

    def _latest_review(self, signal_id: int | None) -> IntelligenceOperatorReview | None:
        if not signal_id:
            return None
        return self.db.execute(
            select(IntelligenceOperatorReview)
            .where(IntelligenceOperatorReview.signal_candidate_id == signal_id)
            .order_by(
                IntelligenceOperatorReview.created_at.desc(), IntelligenceOperatorReview.id.desc()
            )
            .limit(1)
        ).scalar_one_or_none()

    def _operator_overrides(self, signal_id: int | None) -> list[dict[str, Any]]:
        if not signal_id:
            return []
        rows = self.db.execute(
            select(IntelligenceOperatorReview).where(
                IntelligenceOperatorReview.signal_candidate_id == signal_id
            )
        ).scalars()
        return [
            {
                "review_id": row.id,
                "confidence_override": row.confidence_override,
                "publish_override": row.publish_override,
                "review_status": row.review_status,
            }
            for row in rows
            if row.confidence_override is not None or row.publish_override
        ]

    def _operator_review_status(self, signal_id: int | None) -> str:
        review = self._latest_review(signal_id)
        return review.review_status if review else "none"

    def _publication_status(self, signal_id: int | None) -> str:
        if not signal_id:
            return "not_applicable"
        signal = self.db.get(IntelligenceSignalCandidate, signal_id)
        return (
            "published" if signal and signal.published_at else getattr(signal, "status", "unknown")
        )

    def _evidence_sources(self, packet: EvidencePacket) -> dict[str, Any]:
        return {
            key: value
            for key, value in {
                "article_id": packet.article_id,
                "event_id": packet.event_id,
                "impact_id": packet.impact_id,
                "attribution_id": packet.attribution_id,
                "signal_id": packet.signal_id,
            }.items()
            if value is not None
        }

    def _article_id(self, entity_type: str, entity: Any) -> int | None:
        if entity_type == "article":
            return int(entity.id)
        return cast(
            int | None,
            getattr(entity, "article_id", None) or getattr(entity, "primary_article_id", None),
        )

    def _event_id(self, entity_type: str, entity: Any) -> int | None:
        if entity_type == "event":
            return int(entity.id)
        return cast(int | None, getattr(entity, "event_id", None))

    def _impact_id(self, entity_type: str, entity: Any) -> int | None:
        return cast(int | None, getattr(entity, "impact_id", None))

    def _attribution_id(self, entity_type: str, entity: Any) -> int | None:
        return cast(int | None, getattr(entity, "attribution_id", None))

    def _title(self, entity_type: str, entity: Any) -> str:
        return str(
            getattr(entity, "title", None)
            or getattr(entity, "canonical_title", None)
            or f"{entity_type}:{entity.id}"
        )

    def _summary(self, entity_type: str, entity: Any) -> str:
        return str(
            getattr(entity, "summary", None)
            or getattr(entity, "canonical_summary", None)
            or getattr(entity, "summary_text", None)
            or "Evidence packet generated from replayable market-intelligence inputs."
        )

    def _confidence(self, entity_type: str, entity: Any) -> float | None:
        return (
            getattr(entity, "confidence_score", None)
            or getattr(entity, "event_confidence", None)
            or getattr(entity, "impact_confidence_score", None)
        )

    def _source_confidence(self, entity_type: str, entity: Any) -> float | None:
        return (
            getattr(entity, "source_confidence", None)
            or getattr(entity, "source_credibility_score", None)
            or getattr(entity, "credibility_score", None)
        )

    def _low_source_diversity(self, packet: EvidencePacket, entity: Any | None = None) -> bool:
        source_count = getattr(entity, "source_count", None)
        return bool(source_count is not None and source_count < 2)

    def _timeline_step(
        self, step: str, entity_id: int, timestamp: datetime | None, label: str
    ) -> dict[str, Any]:
        return {"step": step, "entity_id": entity_id, "label": label, "timestamp": timestamp}

    def _sanitize(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: (
                    "[redacted]"
                    if any(part in key.lower() for part in SECRET_KEY_PARTS)
                    else self._sanitize(item)
                )
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [self._sanitize(item) for item in value]
        return value

    def _payload_key(self, artifact_type: str) -> str:
        return artifact_type

    def _bounded_packet_type(self, value: str) -> str:
        return (
            value
            if value
            in {
                "article_evidence",
                "event_evidence",
                "impact_evidence",
                "attribution_evidence",
                "signal_evidence",
                "publication_evidence",
            }
            else "other"
        )
