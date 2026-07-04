from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db.models.narrative_memory_snapshot import NarrativeMemorySnapshot
from app.db.models.news_event import NewsEvent
from app.db.models.news_price_impact import NewsPriceImpact
from app.db.models.time_utils import utcnow
from app.services.intelligence.historical_similarity_metrics import (
    NARRATIVE_SNAPSHOTS_GENERATED_TOTAL,
)

INITIAL_NARRATIVES: list[str] = [
    "ETF",
    "Macro",
    "Mining",
    "Lightning",
    "Bitcoin Core",
    "Institutional Adoption",
    "Self Custody",
    "Security",
    "Regulation",
    "Liquidity",
]

NARRATIVE_KEYWORDS: dict[str, list[str]] = {
    "ETF": ["etf", "fund", "inflow", "outflow"],
    "Macro": ["macro", "cpi", "fed", "risk-on", "risk-off", "rate"],
    "Mining": ["miner", "mining", "hashrate", "capitulation"],
    "Lightning": ["lightning"],
    "Bitcoin Core": ["bitcoin core", "core release", "protocol release"],
    "Institutional Adoption": ["institutional", "treasury", "blackrock", "fidelity", "corporate"],
    "Self Custody": ["self custody", "self-custody", "withdrawal", "wallet"],
    "Security": ["security", "hack", "exploit", "custody", "vulnerability"],
    "Regulation": ["sec", "regulation", "regulatory", "approval", "enforcement", "delay"],
    "Liquidity": ["liquidity", "liquidation", "flow", "market depth"],
}

SAFETY_LIMITATIONS = [
    "historical_reference_only",
    "correlation_not_causation",
    "not_financial_advice",
    "evidence_based",
]


class NarrativeMemoryService:
    """Deterministic narrative-memory heat tracking for market-time-machine context."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def track_active_narratives(self, window_hours: int = 24) -> list[dict[str, object]]:
        snapshots = self.build_narrative_snapshot(window_hours=window_hours)
        data = snapshots.get("data", [])
        if not isinstance(data, list):
            return []
        return [
            item
            for item in data
            if isinstance(item, dict) and float(item.get("heat_score", 0.0)) > 0.0
        ]

    def track_narrative_strength(self, narrative: str, window_hours: int = 24) -> dict[str, object]:
        snapshot = self._calculate_snapshot(narrative, window_hours=window_hours)
        return self._payload(snapshot)

    def track_narrative_decay(self, narrative: str) -> dict[str, object]:
        latest = (
            self.db.query(NarrativeMemorySnapshot)
            .filter(NarrativeMemorySnapshot.narrative == narrative)
            .order_by(
                NarrativeMemorySnapshot.snapshot_time.desc(), NarrativeMemorySnapshot.id.desc()
            )
            .first()
        )
        if latest is None:
            return {"narrative": narrative, "decay_score": 1.0, "limitations": SAFETY_LIMITATIONS}
        age_hours = max((utcnow() - latest.snapshot_time).total_seconds() / 3600.0, 0.0)
        decay = max(0.0, min(1.0, age_hours / 72.0))
        return {
            "narrative": narrative,
            "decay_score": round(decay, 6),
            "limitations": SAFETY_LIMITATIONS,
        }

    def build_narrative_snapshot(
        self, window_hours: int = 24, persist: bool = True
    ) -> dict[str, object]:
        rows = [
            self._calculate_snapshot(narrative, window_hours=window_hours)
            for narrative in INITIAL_NARRATIVES
        ]
        if persist:
            self.db.add_all(rows)
            self.db.flush()
            NARRATIVE_SNAPSHOTS_GENERATED_TOTAL.inc(len(rows))
        rows.sort(key=lambda row: (-row.heat_score, row.narrative))
        return {
            "data": [self._payload(row) for row in rows],
            "narratives": [self._payload(row) for row in rows],
            "limitations": SAFETY_LIMITATIONS,
        }

    def history(self, limit: int = 100) -> dict[str, object]:
        rows = (
            self.db.query(NarrativeMemorySnapshot)
            .order_by(
                NarrativeMemorySnapshot.snapshot_time.desc(), NarrativeMemorySnapshot.id.desc()
            )
            .limit(max(0, min(limit, 500)))
            .all()
        )
        return {"data": [self._payload(row) for row in rows], "limitations": SAFETY_LIMITATIONS}

    def _calculate_snapshot(self, narrative: str, window_hours: int) -> NarrativeMemorySnapshot:
        now = utcnow()
        since = now - timedelta(hours=window_hours)
        keywords = NARRATIVE_KEYWORDS[narrative]
        events = [
            event
            for event in self.db.query(NewsEvent).filter(NewsEvent.first_seen_at >= since).all()
            if self._matches(event, keywords)
        ]
        impacts = {
            impact.event_id: impact
            for impact in self.db.query(NewsPriceImpact)
            .filter(NewsPriceImpact.event_id.in_([event.id for event in events] or [0]))
            .all()
        }
        event_count = len(events)
        weighted_impact = self._avg(
            [event.market_impact_score * event.btc_relevance_score for event in events]
        )
        source_quality = self._avg(
            [
                min(1.0, (event.source_count / 3.0 + event.provider_confidence) / 2.0)
                for event in events
            ]
        )
        market_reaction = self._avg(
            [
                min(abs(float(getattr(impact, "change_4h_pct", 0.0) or 0.0)) / 5.0, 1.0)
                for impact in impacts.values()
            ]
        )
        newest_age_hours = min(
            [self._age_hours(now, event.first_seen_at) for event in events], default=window_hours
        )
        time_decay = max(0.0, min(1.0, 1.0 - newest_age_hours / max(window_hours, 1)))
        volume = min(1.0, event_count / 10.0)
        heat = round(
            max(
                0.0,
                min(
                    1.0,
                    volume * 0.25
                    + weighted_impact * 0.25
                    + source_quality * 0.20
                    + market_reaction * 0.15
                    + time_decay * 0.15,
                ),
            ),
            6,
        )
        return NarrativeMemorySnapshot(
            narrative=narrative,
            snapshot_time=now,
            event_count=event_count,
            weighted_impact=round(weighted_impact, 6),
            source_quality=round(source_quality, 6),
            market_reaction=round(market_reaction, 6),
            time_decay=round(time_decay, 6),
            heat_score=heat,
            strength_score=heat,
            decay_score=round(1.0 - time_decay, 6),
            metadata_json={"window_hours": window_hours, "keywords": keywords},
        )

    def _age_hours(self, now: datetime, seen_at: datetime) -> float:
        comparable_now = now.replace(tzinfo=None) if seen_at.tzinfo is None else now
        return float(max((comparable_now - seen_at).total_seconds() / 3600.0, 0.0))

    def _matches(self, event: NewsEvent, keywords: list[str]) -> bool:
        text = f"{event.canonical_title} {event.canonical_summary} {event.event_type} {event.event_category}".lower()
        return any(keyword in text for keyword in keywords)

    def _avg(self, values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    def _payload(self, row: NarrativeMemorySnapshot) -> dict[str, object]:
        return {
            "id": row.id,
            "narrative": row.narrative,
            "snapshot_time": row.snapshot_time,
            "event_count": row.event_count,
            "weighted_impact": row.weighted_impact,
            "source_quality": row.source_quality,
            "market_reaction": row.market_reaction,
            "time_decay": row.time_decay,
            "heat_score": row.heat_score,
            "strength_score": row.strength_score,
            "decay_score": row.decay_score,
            "limitations": SAFETY_LIMITATIONS,
        }
