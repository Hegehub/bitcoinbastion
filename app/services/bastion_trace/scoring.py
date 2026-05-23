from app.schemas.bastion_trace import (
    TraceFactorContribution,
    TraceFreshness,
    TraceScoringInput,
    TraceScoringResult,
    TraceSourceQuality,
)
from app.services.bastion_trace.confidence import compute_confidence
from app.services.bastion_trace.false_positive_guard import apply_false_positive_guard, score_to_band
from app.services.bastion_trace.trace_dna import build_trace_dna

WEIGHTS = {
    "known_high_risk_exposure": 35,
    "suspicious_pattern_signal": 20,
    "privacy_leak_signal": 12,
    "origin_uncertainty": 10,
    "provider_disagreement": 10,
    "stale_evidence": 8,
    "weak_source_quality": 8,
    "node_backed_confirmation": -10,
    "multiple_independent_sources": -8,
    "false_positive_risk": -12,
    "sovereignty_preservation": -6,
}


def _freshness(days: list[int]) -> TraceFreshness:
    if not days:
        return TraceFreshness.UNKNOWN
    d = min(days)
    if d <= 1:
        return TraceFreshness.FRESH
    if d <= 7:
        return TraceFreshness.RECENT
    return TraceFreshness.STALE


def _source_quality(count: int, disagreement: float, baseline: bool) -> TraceSourceQuality:
    if count == 0:
        return TraceSourceQuality.UNKNOWN
    if disagreement > 0.6:
        return TraceSourceQuality.MIXED
    if baseline:
        return TraceSourceQuality.LOW
    if count >= 2:
        return TraceSourceQuality.HIGH
    return TraceSourceQuality.MEDIUM


def score_trace(payload: TraceScoringInput) -> TraceScoringResult:
    factors = payload.factors
    score = 0.0
    contributions: list[TraceFactorContribution] = []
    for factor, weight in WEIGHTS.items():
        value = float(factors.get(factor, 0.0))
        contrib = value * weight
        score += contrib
        direction = "neutral"
        if contrib > 0:
            direction = "increase_risk"
        elif contrib < 0:
            direction = "decrease_risk"
        contributions.append(
            TraceFactorContribution(
                factor=factor,
                value=value,
                weight=weight,
                contribution=contrib,
                direction=direction,
                reason=f"baseline_weight:{weight}",
            )
        )
    score = max(0.0, min(100.0, score))
    freshness = _freshness(payload.evidence_freshness_days)
    disagreement = factors.get("provider_disagreement", 0.0)
    source_quality = _source_quality(payload.independent_source_count, disagreement, payload.baseline_mode)
    confidence, ledger = compute_confidence(
        payload.evidence_count,
        payload.independent_source_count,
        source_quality,
        freshness,
        disagreement,
        factors.get("node_backed_confirmation", 0.0),
        payload.baseline_mode,
    )
    score, guard_reasons = apply_false_positive_guard(
        score,
        confidence,
        payload.evidence_count,
        payload.baseline_mode,
        freshness == TraceFreshness.STALE,
        source_quality in {TraceSourceQuality.LOW, TraceSourceQuality.UNKNOWN},
    )
    band = score_to_band(score, confidence, payload.evidence_count, payload.baseline_mode)
    reasons = list(payload.reason_codes) + list(guard_reasons)
    if payload.evidence_count == 0:
        reasons.append("NO_MEANINGFUL_EVIDENCE")
    if payload.baseline_mode:
        reasons.append("BASELINE_SCORING_ONLY")
    dna = build_trace_dna(
        score,
        factors.get("privacy_leak_signal", 0),
        factors.get("origin_uncertainty", 0),
        disagreement,
        1.0 if freshness == TraceFreshness.STALE else 0.5 if freshness == TraceFreshness.RECENT else 0.0,
        factors.get("sovereignty_preservation", 0),
        min(1.0, payload.evidence_count / 4),
        factors.get("false_positive_risk", 0),
    )
    return TraceScoringResult(
        final_score=score,
        band=band,
        confidence=confidence,
        source_quality=source_quality,
        freshness=freshness,
        trace_dna=dna,
        factor_contributions=contributions,
        confidence_ledger=ledger,
        reason_codes=sorted(set(reasons)),
    )
