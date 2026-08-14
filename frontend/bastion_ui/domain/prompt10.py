# mypy: disable-error-code="attr-defined,arg-type"
"""Feature-54 safe projections for typed historical Market contracts."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from bastion_ui.transport.generated_http import (
    MarketHistoryAttributionsSuccess,
    MarketHistoryNarrativesSuccess,
    MarketHistoryReplayEventSuccess,
    MarketHistorySourcesSuccess,
    MarketHistoryTimelineSuccess,
)


class FrozenViewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class EvidenceLinkViewModel(FrozenViewModel):
    evidence_id: int
    relation: str
    label: str
    verification_status: str


class TimelineItemViewModel(FrozenViewModel):
    event_id: int
    sequence: int
    kind: str
    producer_type: str
    occurred_at: datetime
    observed_at: datetime
    source_name: str
    source_type: str
    title: str
    summary: str
    limitations: tuple[str, ...]
    evidence_links: tuple[EvidenceLinkViewModel, ...]


class TimelineViewModel(FrozenViewModel):
    items: tuple[TimelineItemViewModel, ...]
    next_before_sequence: int | None
    ordering: str


class ReplayViewModel(FrozenViewModel):
    capture_id: str
    schema_version: str
    captured_at: datetime
    effective_at: datetime
    event: TimelineItemViewModel
    digest_algorithm: str
    content_digest: str
    integrity_meaning: str
    limitations: tuple[str, ...]


class AttributionViewModel(FrozenViewModel):
    attribution_id: int
    subject_candle_id: int
    factor_event_id: int | None
    relation: str
    confidence_ratio: Decimal
    explanation: str
    limitations: tuple[str, ...]
    evidence_links: tuple[EvidenceLinkViewModel, ...]


class NarrativeViewModel(FrozenViewModel):
    narrative_id: int
    slug: str
    title: str
    body_plain_text: str
    origin: str
    generated_at: datetime
    confidence_ratio: Decimal
    limitations: tuple[str, ...]


class SourceViewModel(FrozenViewModel):
    source_id: str
    display_name: str
    source_type: str
    category: str
    homepage_url: str | None
    observed_at: datetime | None
    limitations: tuple[str, ...]


def _links(items: object) -> tuple[EvidenceLinkViewModel, ...]:
    return tuple(
        EvidenceLinkViewModel(
            evidence_id=item.evidence_id,
            relation=item.relation.root,
            label=item.label,
            verification_status=item.verification_status,
        )
        for item in items
    )


def _timeline_item(item: object) -> TimelineItemViewModel:
    return TimelineItemViewModel(
        event_id=item.event_id,
        sequence=item.sequence,
        kind=item.kind.root,
        producer_type=item.producer_type,
        occurred_at=item.occurred_at,
        observed_at=item.observed_at,
        source_name=item.source.display_name,
        source_type=item.source.source_type.root,
        title=item.title,
        summary=item.summary,
        limitations=tuple(item.limitations),
        evidence_links=_links(item.evidence_links),
    )


def adapt_timeline(response: MarketHistoryTimelineSuccess) -> TimelineViewModel:
    return TimelineViewModel(
        items=tuple(_timeline_item(item) for item in response.root.items),
        next_before_sequence=response.root.next_before_sequence,
        ordering=response.root.ordering or "occurred_at_desc,event_id_desc",
    )


def adapt_replay(response: MarketHistoryReplayEventSuccess) -> ReplayViewModel:
    item = response.root
    return ReplayViewModel(
        capture_id=str(item.capture_id),
        schema_version=item.schema_version or "market-replay.capture.v1",
        captured_at=item.captured_at,
        effective_at=item.effective_at,
        event=_timeline_item(item.event),
        digest_algorithm=item.integrity.algorithm or "sha256",
        content_digest=item.integrity.content_digest,
        integrity_meaning=item.integrity.meaning or "CONTENT_EQUALITY_ONLY",
        limitations=tuple(item.limitations or ()),
    )


def adapt_attributions(
    response: MarketHistoryAttributionsSuccess,
) -> tuple[AttributionViewModel, ...]:
    return tuple(
        AttributionViewModel(
            attribution_id=item.attribution_id,
            subject_candle_id=item.subject_candle_id,
            factor_event_id=item.factor_event_id,
            relation=item.relation.root,
            confidence_ratio=item.confidence_ratio,
            explanation=item.explanation,
            limitations=tuple(item.limitations or ()),
            evidence_links=_links(item.evidence_links),
        )
        for item in response.root
    )


def adapt_narratives(response: MarketHistoryNarrativesSuccess) -> tuple[NarrativeViewModel, ...]:
    return tuple(
        NarrativeViewModel(
            narrative_id=item.narrative_id,
            slug=item.slug,
            title=item.title,
            body_plain_text=item.body_plain_text,
            origin=item.origin.root,
            generated_at=item.generated_at,
            confidence_ratio=item.confidence_ratio,
            limitations=tuple(item.limitations),
        )
        for item in response.root
    )


def adapt_sources(response: MarketHistorySourcesSuccess) -> tuple[SourceViewModel, ...]:
    return tuple(
        SourceViewModel(
            source_id=item.source_id,
            display_name=item.display_name,
            source_type=item.source_type.root,
            category=item.category,
            homepage_url=str(item.homepage_url) if item.homepage_url is not None else None,
            observed_at=item.observed_at,
            limitations=tuple(item.limitations),
        )
        for item in response.root
    )
