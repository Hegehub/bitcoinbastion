from prometheus_client import Counter, Histogram

from .confidence_bands import confidence_band
from .confidence_contributions import build_contributions
from .delayed_reaction_detector import DelayedReactionDetector
from .false_signal_detector import FalseSignalDetector
from .freshness_weighting import freshness_weight
from .uncertainty_rules import uncertainty_flags

CALCS = Counter("market_intelligence_confidence_calculations_total", "total")
FALSES = Counter("market_intelligence_false_signals_total", "false signals")
DELAYED = Counter("market_intelligence_delayed_reactions_total", "delayed reactions")
UNCERT = Counter("market_intelligence_uncertainty_flags_total", "uncertainty flags")
PROV_DIS = Counter("market_intelligence_provider_disagreement_total", "provider disagreements")
DUR = Histogram("market_intelligence_confidence_duration_seconds", "duration")


class ImpactConfidenceEngine:
    def calculate_impact_confidence(self, *, btc_relevance_score: float, source_credibility_score: float, provider_confidence: float, price_move_strength: float, sentiment_direction_match: float, minutes_to_reaction: int, volatility_context_weight: float, event_confirmation_weight: float, provider_count: int, stale: bool, simultaneous_events: int) -> dict[str, object]:
        CALCS.inc()
        fw = freshness_weight(minutes_to_reaction)
        delayed = DelayedReactionDetector().detect(minutes_to_reaction, event_confirmation_weight > 0.6, sentiment_direction_match > 0.5)
        false_signal = FalseSignalDetector().detect(btc_relevance_score, price_move_strength, provider_confidence, int(event_confirmation_weight * 3))
        vals = {
            "btc_relevance_score": (btc_relevance_score, 0.20),
            "source_credibility_score": (source_credibility_score, 0.15),
            "provider_confidence": (provider_confidence, 0.15),
            "price_move_strength": (price_move_strength, 0.15),
            "sentiment_direction_match": (sentiment_direction_match, 0.10),
            "freshness_weight": (fw, 0.10),
            "volatility_context_weight": (volatility_context_weight, 0.075),
            "event_confirmation_weight": (event_confirmation_weight, 0.075),
        }
        contributions = build_contributions(vals)
        score = sum(float(x["contribution"]) for x in contributions)
        score = max(0.0, min(1.0, score + delayed.confidence_adjustment - false_signal.confidence_penalty))
        flags = uncertainty_flags(provider_confidence, provider_count, stale, volatility_context_weight < 0.9, simultaneous_events)
        if false_signal.detected:
            FALSES.inc()
        if delayed.detected:
            DELAYED.inc()
        if "provider_disagreement" in flags:
            PROV_DIS.inc()
        for _ in flags:
            UNCERT.inc()
        return {
            "confidence_score": score,
            "confidence_band": confidence_band(score),
            "confidence_contributions": contributions,
            "degradation_factors": flags + (["false_signal_detected"] if false_signal.detected else []),
            "uncertainty_flags": flags,
            "freshness_weight": fw,
            "provider_confidence": provider_confidence,
            "direction_match": sentiment_direction_match > 0.5,
            "delayed_reaction_detected": delayed.detected,
            "false_signal_detected": false_signal.detected,
            "explanation_summary": "Correlation-based confidence computed from relevance, source, provider, price move and timing factors.",
            "limitation": "Correlation-based attribution is not proof of causation.",
        }
