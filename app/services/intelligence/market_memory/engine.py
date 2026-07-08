from __future__ import annotations

from dataclasses import asdict
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.historical_event_similarity import HistoricalEventSimilarity
from app.db.models.market_memory_record import MarketMemoryRecord as MarketMemoryRecordModel
from app.services.intelligence.historical_similarity_engine import (
    HistoricalSimilarityEngine as LegacyHistoricalSimilarityEngine,
)
from app.services.intelligence.market_memory.fingerprint_builder import EventFingerprintBuilder
from app.services.intelligence.market_memory.pattern_matcher import PatternMatcher
from app.services.intelligence.market_memory.safety import MARKET_MEMORY_SAFETY_LIMITATIONS
from app.services.intelligence.market_memory.statistics import PatternStatisticsService
from app.services.intelligence.market_memory.types import SimilarityResult
from app.services.intelligence.market_memory_service import MarketMemoryService


class HistoricalSimilarityEngine:
    """Production Market Memory facade over fingerprinting, patterns, ranking, and replay."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.legacy = LegacyHistoricalSimilarityEngine(db)
        self.fingerprints = EventFingerprintBuilder(db)
        self.patterns = PatternMatcher(db)
        self.statistics = PatternStatisticsService(db)
        self.memory = MarketMemoryService(db)

    def find_similar_events(self, event_id: int, limit: int = 10) -> dict[str, Any]:
        fingerprint = self.fingerprints.build(event_id)
        payload = self.legacy.find_similar_events(event_id, limit=limit)
        pattern_matches = self.patterns.match_event(event_id)
        for match in pattern_matches[:1]:
            self._persist_memory(
                event_id, match.pattern_id, match.confidence_score, match.confidence_score
            )
        primary_pattern = pattern_matches[0].pattern_slug if pattern_matches else None
        reaction_summary = (
            self.statistics.payload(self.statistics.compute(primary_pattern))
            if primary_pattern
            else None
        )
        payload["event_fingerprint"] = asdict(fingerprint) if fingerprint else None
        payload["pattern_matches"] = [asdict(match) for match in pattern_matches]
        payload["historical_reaction_summary"] = reaction_summary
        payload["limitations"] = self._safety(payload.get("limitations", []))
        payload["safety_rules"] = MARKET_MEMORY_SAFETY_LIMITATIONS.copy()
        return payload

    def ranked_results(self, event_id: int, limit: int = 10) -> list[SimilarityResult]:
        self.find_similar_events(event_id, limit=limit)
        rows = (
            self.db.query(HistoricalEventSimilarity)
            .filter(HistoricalEventSimilarity.event_id == event_id)
            .order_by(
                HistoricalEventSimilarity.similarity_score.desc(),
                HistoricalEventSimilarity.id.asc(),
            )
            .limit(limit)
            .all()
        )
        results: list[SimilarityResult] = []
        for row in rows:
            explanation = row.explanation_json if isinstance(row.explanation_json, dict) else {}
            raw_reasons = explanation.get("reasons", [])
            reason_codes = (
                [str(item) for item in raw_reasons] if isinstance(raw_reasons, list) else []
            )
            results.append(
                SimilarityResult(
                    event_id=row.event_id,
                    similar_event_id=row.similar_event_id,
                    similarity_score=row.similarity_score,
                    confidence_score=min(row.similarity_score, 1.0),
                    reason_codes=reason_codes,
                )
            )
        return results

    def replay(self, event_id: int, limit: int = 10) -> dict[str, Any]:
        payload = self.find_similar_events(event_id, limit=limit)
        candidates = payload.get("similar_events", [])
        return {
            "event_analyzed": payload.get("current_event"),
            "candidate_events": candidates,
            "similarity_scores": [
                {"event_id": item.get("event_id"), "score": item.get("similarity_score")}
                for item in candidates
            ],
            "pattern_assignment": payload.get("pattern_matches", []),
            "reason_codes": [
                item.get("explanation", {}).get("reasons", [])
                for item in candidates
                if isinstance(item, dict)
            ],
            "final_ranking": [
                item.get("event_id") for item in candidates if isinstance(item, dict)
            ],
            "limitations": MARKET_MEMORY_SAFETY_LIMITATIONS.copy(),
        }

    def _persist_memory(
        self, event_id: int, pattern_id: int, memory_score: float, confidence: float
    ) -> None:
        self.db.add(
            MarketMemoryRecordModel(
                event_id=event_id,
                pattern_id=pattern_id,
                memory_type="pattern_assignment",
                memory_score=memory_score,
                confidence_score=confidence,
            )
        )
        self.db.flush()

    def _safety(self, limitations: list[object]) -> list[str]:
        output = [str(item) for item in limitations]
        for item in MARKET_MEMORY_SAFETY_LIMITATIONS:
            if item not in output:
                output.append(item)
        return output
