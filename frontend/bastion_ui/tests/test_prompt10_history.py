from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from bastion_ui.domain.prompt10 import (
    adapt_attributions,
    adapt_narratives,
    adapt_replay,
    adapt_sources,
    adapt_timeline,
)
from bastion_ui.transport.generated_http import (
    MarketHistoryAttributionsSuccess,
    MarketHistoryNarrativesSuccess,
    MarketHistoryReplayEventSuccess,
    MarketHistorySourcesSuccess,
    MarketHistoryTimelineSuccess,
)
from bastion_ui.transport.generated_schemas import (
    AttributionRelation,
    BrowserSafeMarketSourceOut,
    MarketAttributionOut,
    MarketEvidenceLink,
    MarketEvidenceRelation,
    MarketNarrativeOut,
    MarketSourceType,
    MarketReplayCaptureOut,
    MarketSourceRef,
    MarketTimelineEventOut,
    MarketTimelinePageOut,
    NarrativeOrigin,
    ReplayIntegrityOut,
    TimelineKind,
)


def _event() -> MarketTimelineEventOut:
    now = datetime(2026, 8, 12, 12, tzinfo=UTC)
    return MarketTimelineEventOut(
        event_id=7,
        sequence=7,
        kind=TimelineKind(root="NEWS"),
        producer_type="news_event",
        occurred_at=now,
        observed_at=now,
        source=MarketSourceRef(
            source_id="timeline:news",
            display_name="NEWS",
            source_type=MarketSourceType(root="NEWS"),
        ),
        title="Stored event",
        summary="Observed report",
        related_signal_id=None,
        related_candle_id=None,
        evidence_links=[
            MarketEvidenceLink(
                evidence_id=4,
                relation=MarketEvidenceRelation(root="RELATED_EVIDENCE"),
                label="Related packet",
                linked_at=now,
                verification_status="NOT_REQUESTED",
            )
        ],
        limitations=["Correlation is not proof of causation."],
    )


def test_typed_timeline_and_replay_copy_backend_semantics_without_inference() -> None:
    event = _event()
    timeline = adapt_timeline(
        MarketHistoryTimelineSuccess(
            root=MarketTimelinePageOut(
                items=[event],
                limit=50,
                next_before_sequence=None,
                ordering="occurred_at_desc,event_id_desc",
            )
        )
    )
    replay = adapt_replay(
        MarketHistoryReplayEventSuccess(
            root=MarketReplayCaptureOut(
                capture_id=UUID("12a728ad-f45e-4e21-9167-56f6633f0baf"),
                schema_version="market-replay.capture.v1",
                captured_at=event.observed_at,
                effective_at=event.occurred_at,
                event=event,
                integrity=ReplayIntegrityOut(
                    algorithm="sha256", content_digest="a" * 64, meaning="CONTENT_EQUALITY_ONLY"
                ),
                historical=True,
                limitations=["Digest proves equality only."],
            )
        )
    )
    assert timeline.items[0].kind == "NEWS"
    assert timeline.ordering == "occurred_at_desc,event_id_desc"
    assert replay.integrity_meaning == "CONTENT_EQUALITY_ONLY"
    assert replay.event.title == "Stored event"


def test_attribution_narrative_source_and_evidence_remain_distinct() -> None:
    now = datetime(2026, 8, 12, 12, tzinfo=UTC)
    attribution = adapt_attributions(
        MarketHistoryAttributionsSuccess(
            root=[
                MarketAttributionOut(
                    attribution_id=1,
                    subject_candle_id=2,
                    factor_event_id=3,
                    relation=AttributionRelation(root="CORRELATION_CANDIDATE"),
                    confidence_ratio=Decimal("0.4"),
                    explanation="Backend candidate.",
                    limitations=["Not causal."],
                    evidence_links=[],
                )
            ]
        )
    )[0]
    narrative = adapt_narratives(
        MarketHistoryNarrativesSuccess(
            root=[
                MarketNarrativeOut(
                    narrative_id=1,
                    slug="stored",
                    title="Stored",
                    body_plain_text="Plain text only.",
                    origin=NarrativeOrigin(root="STORED_BACKEND_RECORD"),
                    generated_at=now,
                    confidence_ratio=Decimal("0.5"),
                    limitations=["Analytical narrative."],
                )
            ]
        )
    )[0]
    source = adapt_sources(
        MarketHistorySourcesSuccess(
            root=[
                BrowserSafeMarketSourceOut(
                    source_id="source-1",
                    display_name="Safe",
                    source_type=MarketSourceType(root="NEWS"),
                    category="market_media",
                    homepage_url="https://example.com/",
                    observed_at=now,
                    limitations=[],
                )
            ]
        )
    )[0]
    assert attribution.relation == "CORRELATION_CANDIDATE"
    assert attribution.evidence_links == ()
    assert narrative.body_plain_text == "Plain text only."
    assert source.homepage_url == "https://example.com/"


def test_prompt10_production_paths_do_not_parse_generic_payloads() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    sources = "\n".join(
        (root / path).read_text()
        for path in (
            "domain/prompt10.py",
            "state/prompt10_state.py",
            "components/prompt10_screens.py",
        )
    )
    assert "dict[str, Any]" not in sources
    assert "payload_json" not in sources
    assert "caused by" not in sources.casefold()
