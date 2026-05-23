from app.schemas.bastion_trace import TraceDNA


def _norm(value: float) -> float:
    return max(0.0, min(1.0, value))


def build_trace_dna(
    final_score: float,
    privacy: float,
    origin: float,
    disagreement: float,
    freshness_decay: float,
    sovereignty: float,
    evidence_strength: float,
    fp_risk: float,
) -> TraceDNA:
    return TraceDNA(
        risk=_norm(final_score / 100),
        privacy_exposure=_norm(privacy),
        origin_uncertainty=_norm(origin),
        provider_disagreement=_norm(disagreement),
        freshness_decay=_norm(freshness_decay),
        sovereignty=_norm(sovereignty),
        evidence_strength=_norm(evidence_strength),
        false_positive_risk=_norm(fp_risk),
    )
