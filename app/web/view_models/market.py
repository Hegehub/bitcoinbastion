from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from app.schemas.market_time_machine_web import (
    CandleAttributionDTO,
    MarketTimelineDTO,
    NewsMarkerDTO,
)
from app.web.market_time_machine_service import SAFETY_LIMITATIONS

MARKER_ICONS = {
    "positive": "🟢",
    "negative": "🔴",
    "uncertain": "🟡",
    "security": "⚠️",
    "regulatory": "🏛",
    "institutional": "🏦",
    "macro": "🌐",
    "bitcoin_core": "₿",
    "lightning": "⚡",
    "mining": "⛏",
}

MARKER_CANONICAL_TYPES = {
    "positive": "positive_news",
    "negative": "negative_news",
    "uncertain": "uncertain_news",
    "security": "security_shock",
    "regulatory": "regulatory_event",
    "institutional": "institutional_event",
    "macro": "macro_event",
    "bitcoin_core": "bitcoin_core_event",
    "lightning": "lightning_event",
    "mining": "mining_event",
}

NARRATIVE_ORDER = [
    "ETF",
    "Fed",
    "Macro",
    "Mining",
    "Lightning",
    "Bitcoin Core",
    "Security",
    "Institutional",
    "Sovereignty",
]

SAFETY_FLAGS = {
    "correlation_not_causation": True,
    "evidence_based": True,
    "operator_reviewed": False,
    "provider_health_visible": True,
}


@dataclass(frozen=True)
class MarketPageFrame:
    slug: str
    title: str
    subtitle: str
    filter_name: str = "all"


PAGE_FRAMES = {
    "timeline": MarketPageFrame(
        "timeline",
        "Market Timeline",
        "Windowed market memory across candles, news events, signals, shocks, narrative shifts, and operator publications.",
    ),
    "time-machine": MarketPageFrame(
        "time-machine",
        "Market Time Machine",
        "Select a date and timeframe, then inspect candles, markers, attribution, evidence, replay, and limitations.",
    ),
    "signals": MarketPageFrame(
        "signals",
        "Signals",
        "Published, pending-review, held, rejected, false-positive, and expired intelligence signals.",
    ),
    "evidence": MarketPageFrame(
        "evidence",
        "Evidence",
        "Evidence packets, confidence breakdowns, provider/source snapshots, and replay timelines.",
    ),
    "narratives": MarketPageFrame(
        "narratives",
        "Narratives",
        "Narrative heatmap strength, direction, confidence, and historical frequency.",
    ),
    "sources": MarketPageFrame(
        "sources",
        "Sources",
        "Source health, reputation, latency, failure count, first-mover score, and signal quality.",
    ),
    # Backward-compatible aliases from Task 43.
    "candles": MarketPageFrame("time-machine", "Market Time Machine", "Candle investigation view."),
    "events": MarketPageFrame("timeline", "Market Timeline", "Classified market events."),
    "news": MarketPageFrame("timeline", "Market Timeline", "Canonical news intelligence."),
    "shock-index": MarketPageFrame("timeline", "Market Timeline", "News shock context."),
}


def build_market_dto(
    dto: MarketTimelineDTO,
    *,
    selected_timeframe: str = "1h",
    selected_date: str | None = None,
    api_payload: dict[str, object] | None = None,
    db: object | None = None,
) -> dict[str, Any]:
    """Build a template-facing DTO from service/API payloads only.

    The view model intentionally contains no database reads. Routes hand it
    server-side API/service payloads, and templates consume a stable frontend
    contract.
    """

    _ = db
    api_payload = api_payload or {}
    candles = [_chart_candle(candle) for candle in dto.candles]
    markers = [_chart_marker(marker) for marker in dto.chart_markers]
    selected_candle = candles[-1] if candles else None
    selected_event = markers[0] if markers else None
    narrative_summary = _narrative_summary(dto.narrative_strength)
    shock_index = _shock_index(dto.chart_markers)
    source_summary = _as_mapping(api_payload.get("source_summary"))
    provider_health = _as_mapping(source_summary.get("provider_health")) or _empty_provider_health()
    signals = _as_mapping(api_payload.get("signal_summary"))
    evidence_packets = _as_mapping(api_payload.get("evidence_summary"))
    replay_requests = _as_mapping(api_payload.get("evidence_replay_requests"))
    evidence_summary = _evidence_summary(dto, selected_candle, selected_event, evidence_packets)
    historical_matches = (selected_candle or {}).get(
        "similarity_preview"
    ) or dto.similarity_preview[:5]
    replay_timeline = _replay_timeline(dto.timeline_items, replay_requests)
    return {
        "market_timeline": dto.model_dump(),
        "timeline_events": dto.timeline_items,
        "chart_data": {
            "timeframe": selected_timeframe,
            "candles": candles,
            "markers": markers,
            "supports": [
                "zoom",
                "pan",
                "hover",
                "candle_selection",
                "marker_rendering",
                "responsive_resize",
            ],
            "timeline_supports": [
                "scroll",
                "filter",
                "event_grouping",
                "windowed_rendering",
                "pagination",
            ],
        },
        "marker_data": markers,
        "candle_details": selected_candle,
        "selected_candle": selected_candle,
        "selected_event": selected_event,
        "attribution_details": (selected_candle or {}).get("top_attribution", {}),
        "historical_matches": historical_matches[:5],
        "evidence_summary": evidence_summary,
        "replay_summary": replay_timeline,
        "source_summary": source_summary
        or {"items": [], "limitations": SAFETY_LIMITATIONS + ["Source registry unavailable."]},
        "shock_index": shock_index,
        "shock_index_summary": shock_index,
        "narrative_summary": narrative_summary,
        "provider_health": provider_health,
        "signal_summary": signals or _empty_signal_summary(dto),
        "recent_signals": _signal_items(signals, dto),
        "dashboard_cards": _dashboard_cards(
            api_payload,
            shock_index,
            narrative_summary,
            provider_health,
            signals,
            evidence_packets,
            replay_requests,
            selected_event,
        ),
        "timeline_items": dto.timeline_items,
        "replay_timeline": replay_timeline,
        "safety_flags": SAFETY_FLAGS,
        "limitations": _merge_limitations(dto.limitations),
        "selected_timeframe": selected_timeframe,
        "selected_date": selected_date or date.today().isoformat(),
        "refresh": {"enabled": False, "future_live_refresh_ready": True, "interval_seconds": 60},
    }


def page_frame(slug: str) -> MarketPageFrame:
    return PAGE_FRAMES.get(slug, PAGE_FRAMES["timeline"])


def _chart_candle(candle: CandleAttributionDTO) -> dict[str, Any]:
    explanation_items = [
        {"title": event.get("title", "Candidate event"), "confidence": event.get("confidence", 0.0)}
        for event in candle.candidate_events[:3]
    ]
    signal_items = [
        event
        for event in candle.candidate_events
        if str(event.get("title", "")).lower().find("signal") >= 0
    ][:3]
    combined = (
        "Candidate factors are correlated with this candle, but causal certainty is not claimed."
        if explanation_items
        else "No candidate factors are available for this candle."
    )
    return {
        **candle.model_dump(),
        "price_movement": candle.price_change_pct,
        "top_candidate_events": explanation_items,
        "top_candidate_signals": signal_items,
        "likely_factors": explanation_items,
        "combined_explanation": combined,
        "replay_url": f"/market/timeline?candle_id={candle.id}",
        "evidence_url": f"/api/v1/intelligence/candles/{candle.id}/evidence",
        "replay_available_label": (
            "Replay Available" if candle.replay_available else "Replay Unavailable"
        ),
    }


def _chart_marker(marker: NewsMarkerDTO) -> dict[str, Any]:
    raw = marker.model_dump()
    marker_type = _normalize_marker_type(marker.marker_type)
    icon = MARKER_ICONS.get(marker_type, "🟡")
    return {
        **raw,
        "icon": icon,
        "canonical_type": MARKER_CANONICAL_TYPES.get(marker_type, "uncertain_news"),
        "aria_label": f"{icon} {marker.title} marker at {marker.timestamp}",
        "evidence_available": marker.evidence_packet_id is not None,
        "evidence_url": (
            f"/evidence/{marker.evidence_packet_id}" if marker.evidence_packet_id else ""
        ),
        "replay_url": f"/market/timeline?event_id={marker.event_id}" if marker.event_id else "",
        "similar_events_url": (
            f"/market/timeline?similar_to={marker.event_id}" if marker.event_id else ""
        ),
    }


def _normalize_marker_type(value: str) -> str:
    value = value.replace("_event", "").replace("_news", "")
    if value == "security_shock":
        return "security"
    if value == "bitcoin_core_event":
        return "bitcoin_core"
    if value == "lightning_or_core_event":
        return "lightning"
    return value


def _narrative_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_name = {str(row.get("narrative", "")).lower(): row for row in rows}
    summary = []
    for name in NARRATIVE_ORDER:
        row = by_name.get(name.lower(), {})
        strength = float(row.get("strength", 0.0) or 0.0)
        frequency = row.get("recent_activity") or row.get("historical_frequency") or 0
        summary.append(
            {
                "narrative": name,
                "strength": strength,
                "direction": row.get("direction")
                or row.get("historical_trend")
                or "insufficient_data",
                "trend": row.get("historical_trend") or row.get("direction") or "insufficient_data",
                "confidence": min(max(strength, 0.0), 1.0),
                "historical_frequency": frequency,
            }
        )
    return summary


def _shock_index(markers: list[NewsMarkerDTO]) -> dict[str, Any]:
    if not markers:
        score = 0
    else:
        weighted = sum(
            (marker.impact_confidence or marker.confidence or 0.0)
            * (10 - min(marker.marker_priority, 9))
            for marker in markers[:25]
        )
        score = int(min(100, max(0, weighted * 4)))
    if score < 20:
        regime = "Quiet"
    elif score < 50:
        regime = "Active"
    elif score < 75:
        regime = "High Impact"
    else:
        regime = "Shock Regime"
    contributors = [
        {
            "title": marker.title,
            "type": MARKER_CANONICAL_TYPES.get(
                _normalize_marker_type(marker.marker_type), "uncertain_news"
            ),
            "confidence": marker.impact_confidence or marker.confidence or 0.0,
        }
        for marker in markers[:5]
    ]
    return {
        "score": score,
        "regime": regime,
        "current_value": score,
        "recent_history": [max(0, score - 8), max(0, score - 4), score],
        "dominant_contributors": contributors,
        "bands": ["0-20 Quiet", "20-50 Active", "50-75 High Impact", "75-100 Shock Regime"],
        "explanation": "Index reflects classified news pressure and impact confidence; it is not a prediction.",
    }


def _evidence_summary(
    dto: MarketTimelineDTO,
    selected_candle: dict[str, Any] | None,
    selected_event: dict[str, Any] | None,
    evidence_packets: dict[str, Any],
) -> dict[str, Any]:
    packet_id = (selected_event or {}).get("evidence_packet_id")
    packet_items = _as_list(evidence_packets.get("items"))
    latest_packet = packet_items[0] if packet_items else {}
    return {
        "summary": dto.evidence_summary.get("source")
        or latest_packet.get("summary")
        or "Evidence packet status is visible for selected entities.",
        "sources": (selected_event or {}).get(
            "evidence_count", latest_packet.get("artifact_count", 0)
        ),
        "provider_confidence": (selected_event or {}).get("provider_confidence")
        or (selected_candle or {}).get("provider_confidence")
        or latest_packet.get("provider_confidence", 0.0),
        "confidence_breakdown": (selected_candle or {}).get("confidence_breakdown", {}),
        "provider_snapshot": {
            "provider_confidence": (selected_event or {}).get("provider_confidence", 0.0),
            "degraded_visible": True,
        },
        "source_snapshot": {
            "source": (selected_event or {}).get("source", "unknown"),
            "source_confidence": (selected_event or {}).get("source_confidence", 0.0),
        },
        "replay_available": bool(
            (selected_event or {}).get("replay_available")
            or (selected_candle or {}).get("replay_available")
        ),
        "limitations": _merge_limitations(
            dto.limitations + _as_list(evidence_packets.get("limitations"))
        ),
        "operator_review_status": dto.operator_status.get("status", "display_only"),
        "packet_id": packet_id or latest_packet.get("packet_id"),
        "export_json_url": f"/api/v1/evidence/packets/{packet_id}" if packet_id else "",
        "open_replay_url": (selected_event or {}).get("replay_url")
        or (selected_candle or {}).get("replay_url")
        or "",
        "relationships_url": (
            f"/api/v1/evidence/packets/{packet_id}/relationships" if packet_id else ""
        ),
        "packets": packet_items,
        "items": packet_items,
    }


def _replay_timeline(
    items: list[dict[str, Any]], replay_requests: dict[str, Any]
) -> list[dict[str, Any]]:
    timeline = [
        {
            "timeline": item.get("timestamp"),
            "evidence_chain": item.get("evidence_refs", []),
            "input_entities": [item.get("related_event_id"), item.get("related_candle_id")],
            "derived_entities": [item.get("related_signal_id")],
            "hashes": [],
            "confidence": item.get("confidence", 0.0),
            "policy_decisions": item.get("policy_decisions", []),
            "operator_actions": [],
            "publication_status": item.get("status", "visible"),
            "operator_review": item.get("status", "visible"),
            "success": True,
        }
        for item in items[:12]
    ]
    for replay in _as_list(replay_requests.get("items"))[:12]:
        timeline.append(
            {
                "timeline": replay.get("started_at"),
                "evidence_chain": [replay.get("step")],
                "input_entities": [replay.get("entity_type"), replay.get("entity_id")],
                "derived_entities": [],
                "hashes": [replay.get("input_hash"), replay.get("output_hash")],
                "confidence": replay.get("confidence", 0.0),
                "policy_decisions": replay.get("policy_decisions", []),
                "operator_actions": replay.get("operator_actions", []),
                "publication_status": replay.get("publication_status", "unknown"),
                "operator_review": "visible",
                "success": replay.get("success", False),
                "error_code": replay.get("error_code"),
            }
        )
    return timeline[:20]


def _dashboard_cards(
    api_payload: dict[str, object],
    shock_index: dict[str, Any],
    narratives: list[dict[str, Any]],
    provider_health: dict[str, Any],
    signals: dict[str, Any],
    evidence_packets: dict[str, Any],
    replay_requests: dict[str, Any],
    selected_event: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    btc_price = _as_mapping(api_payload.get("btc_price"))
    operator_queue = _as_mapping(signals.get("operator_queue"))
    return [
        {
            "title": "BTC Price",
            "value": btc_price.get("price_usd") or "unknown",
            "detail": f"Provider confidence {float(btc_price.get('provider_confidence', 0.0) or 0.0):.2f}",
            "href": "/market/time-machine",
            "refresh_ready": True,
        },
        {
            "title": "News Shock Index",
            "value": f"{shock_index['score']} / 100",
            "detail": shock_index["regime"],
            "href": "/market/timeline",
            "refresh_ready": True,
        },
        {
            "title": "Active Narratives",
            "value": sum(1 for item in narratives if item["strength"] > 0),
            "detail": "Narrative heatmap",
            "href": "/market/narratives",
            "refresh_ready": True,
        },
        {
            "title": "Latest High Impact Event",
            "value": (selected_event or {}).get("title", "No high-impact event"),
            "detail": (selected_event or {}).get("canonical_type", "Event context unavailable"),
            "href": "/market/timeline",
            "refresh_ready": True,
        },
        {
            "title": "Latest Published Signal",
            "value": (
                _as_mapping(signals.get("latest_published_signal")).get("title")
                or "No published signal"
            ),
            "detail": "Signals remain operator governed",
            "href": "/market/signals",
            "refresh_ready": True,
        },
        {
            "title": "Provider Health",
            "value": f"{provider_health.get('degraded_count', 0)} degraded",
            "detail": f"Confidence {float(provider_health.get('provider_confidence', 0.0) or 0.0):.2f}",
            "href": "/market/sources",
            "refresh_ready": True,
        },
        {
            "title": "Operator Queue",
            "value": operator_queue.get("pending_count", 0),
            "detail": "Review-required items",
            "href": "/market/signals?status=pending_review",
            "refresh_ready": True,
        },
        {
            "title": "Evidence Replay Requests",
            "value": len(_as_list(replay_requests.get("items"))),
            "detail": f"{replay_requests.get('failure_count', 0)} replay failures visible",
            "href": "/market/evidence",
            "refresh_ready": True,
        },
    ]


def _signal_items(signals: dict[str, Any], dto: MarketTimelineDTO) -> list[dict[str, Any]]:
    items = _as_list(signals.get("items"))
    if items:
        return items
    return [signal.model_dump() for signal in dto.signals]


def _empty_signal_summary(dto: MarketTimelineDTO) -> dict[str, Any]:
    return {
        "items": [signal.model_dump() for signal in dto.signals],
        "counts": {
            "published": 0,
            "pending_review": 0,
            "held": 0,
            "rejected": 0,
            "false_positive": 0,
            "expired": 0,
        },
        "latest_published_signal": None,
        "operator_queue": {"pending_count": 0, "reviews": []},
        "limitations": SAFETY_LIMITATIONS,
    }


def _merge_limitations(limitations: list[str]) -> list[str]:
    return list(
        dict.fromkeys(
            [
                *SAFETY_LIMITATIONS,
                *limitations,
                "correlation_not_causation",
                "evidence_based",
                "operator_reviewed",
                "provider_health_visible",
            ]
        )
    )


def _empty_provider_health() -> dict[str, Any]:
    return {
        "news_providers": 0,
        "market_providers": 0,
        "provider_confidence": 0.0,
        "degraded_sources": [],
        "degraded_count": 0,
        "provider_health_visible": True,
        "limitations": SAFETY_LIMITATIONS,
    }


def _as_mapping(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []
