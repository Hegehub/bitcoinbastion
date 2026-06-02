from __future__ import annotations

from dataclasses import asdict
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.news_event import NewsEvent
from app.db.models.time_utils import utcnow
from app.services.intelligence.market_memory.engine import HistoricalSimilarityEngine
from app.services.intelligence.market_memory.safety import MARKET_MEMORY_SAFETY_LIMITATIONS
from app.services.intelligence.market_memory.types import MarketMemoryEvidence


class MarketMemoryEvidenceBuilder:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.engine = HistoricalSimilarityEngine(db)

    def build(self, event_id: int, limit: int = 10) -> MarketMemoryEvidence:
        payload = self.engine.find_similar_events(event_id, limit=limit)
        source_events = []
        for item in payload.get("similar_events", []):
            if isinstance(item, dict):
                event = self.db.get(NewsEvent, item.get("event_id"))
                source_events.append(
                    {
                        "event_id": item.get("event_id"),
                        "title": item.get("title") or (event.canonical_title if event else ""),
                        "date": item.get("date"),
                        "reaction_4h_pct": item.get("reaction_4h_pct"),
                    }
                )
        evidence = MarketMemoryEvidence(
            event_id=event_id,
            source_events=source_events,
            similarity_calculations=[
                {
                    "similar_event_id": item.get("event_id"),
                    "similarity_score": item.get("similarity_score"),
                    "components": item.get("explanation", {}).get("components", {}),
                    "reason_codes": item.get("explanation", {}).get("reasons", []),
                }
                for item in payload.get("similar_events", [])
                if isinstance(item, dict)
            ],
            pattern_matches=list(payload.get("pattern_matches", payload.get("pattern_reasoning", []))),
            historical_reaction_summary=dict(payload.get("historical_reaction_summary") or payload.get("historical_reaction_profile") or {}),
            limitations=self._safety(payload.get("limitations", [])),
            provider_confidence=float(payload.get("provider_confidence", 0.0) or 0.0),
            generated_at=utcnow(),
        )
        return evidence

    def payload(self, event_id: int, limit: int = 10) -> dict[str, Any]:
        return asdict(self.build(event_id, limit=limit))

    def _safety(self, limitations: list[object]) -> list[str]:
        output = [str(item) for item in limitations]
        for item in MARKET_MEMORY_SAFETY_LIMITATIONS:
            if item not in output:
                output.append(item)
        return output
