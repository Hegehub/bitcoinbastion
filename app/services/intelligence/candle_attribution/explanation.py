from app.db.models.btc_candle import BTCCandle
from app.services.intelligence.candle_attribution.scoring import ScoredCandidate

LIMITATION_CORRELATION = "Correlation is not proof of causation."


class CandleExplanationBuilder:
    """Build operator-safe attribution summaries and limitations."""

    def build(
        self, candle: BTCCandle, candidate: ScoredCandidate, candidate_count: int
    ) -> tuple[str, dict[str, object], dict[str, object]]:
        title = candidate.event.canonical_title
        summary = (
            f"{candidate.candidate_category} candidate event may be relevant to the "
            f"{candle.timeframe} BTC candle context; attribution remains correlation-based."
        )
        reasoning = [
            "Candidate was found inside or near the configured candle attribution window.",
            f"BTC relevance score contributed {candidate.event.btc_relevance_score:.2f}.",
            f"Market impact score contributed {candidate.impact_score:.2f}.",
            f"Time distance weight contributed {candidate.time_distance_weight:.2f}.",
        ]
        if candidate.direction_match:
            reasoning.append("Event sentiment direction matched the candle direction.")
        else:
            reasoning.append("Event sentiment did not clearly match the candle direction.")
        limitations = [
            LIMITATION_CORRELATION,
            "Other market factors may have contributed to this candle.",
            "Attribution confidence is capped to avoid fake certainty.",
        ]
        explanation = {
            "summary": summary,
            "candidate_count": candidate_count,
            "top_candidate": {
                "event_id": candidate.event.id,
                "article_id": candidate.article_id,
                "title": title,
                "confidence": candidate.confidence_score,
            },
            "reasoning": reasoning,
            "evidence": {
                "time_distance_seconds": candidate.time_distance_seconds,
                "price_move_pct": candidate.price_move_pct,
                "provider_confidence": candidate.provider_confidence,
                "source_confidence": candidate.source_confidence,
            },
            "limitations": limitations,
        }
        return summary, explanation, {"limitations": limitations}

    def build_empty(self, candle: BTCCandle) -> dict[str, object]:
        return {
            "summary": f"No candidate news events were found for the {candle.timeframe} BTC candle attribution window.",
            "candidate_count": 0,
            "limitations": [
                LIMITATION_CORRELATION,
                "No nearby news events were available for ranking.",
            ],
        }
