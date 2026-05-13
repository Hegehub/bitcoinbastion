from app.schemas.common import ExplainabilityContractOut


def build_explainability_contract(
    *,
    domain: str,
    confidence: float,
    freshness: dict[str, object] | None = None,
    source_type: str = "unknown",
    provider_name: str = "unknown",
    is_mock: bool = False,
    is_fallback: bool = False,
    limitations: list[str] | None = None,
    signals: dict[str, object] | None = None,
) -> dict[str, object]:
    return ExplainabilityContractOut(
        domain=domain,
        source_type=source_type,
        provider_name=provider_name,
        is_mock=is_mock,
        is_fallback=is_fallback,
        confidence=confidence,
        freshness=freshness or {},
        limitations=limitations or [],
        signals=signals or {},
    ).model_dump()


def append_evidence_step(
    *,
    chain: list[dict[str, object]] | None,
    domain: str,
    reference: str,
    confidence: float,
    source_type: str = "unknown",
    details: dict[str, object] | None = None,
) -> list[dict[str, object]]:
    next_chain = list(chain or [])
    next_chain.append(
        {
            "domain": domain,
            "reference": reference,
            "confidence": round(max(0.0, min(1.0, float(confidence))), 4),
            "source_type": source_type,
            "details": details or {},
        }
    )
    return next_chain


def propagate_confidence(
    *,
    base_confidence: float,
    freshness_band: str = "unknown",
    is_fallback: bool = False,
    is_synthetic: bool = False,
) -> float:
    confidence = max(0.0, min(1.0, float(base_confidence)))
    freshness_penalty = {
        "fresh": 0.0,
        "recent": 0.03,
        "aging": 0.06,
        "stale": 0.12,
        "very_stale": 0.2,
        "unknown": 0.08,
    }.get(str(freshness_band), 0.1)
    confidence -= freshness_penalty
    if is_fallback:
        confidence -= 0.14
    if is_synthetic:
        confidence -= 0.12
    return round(max(0.05, min(0.95, confidence)), 4)


def build_audit_packet(
    *,
    packet_type: str,
    evidence_refs: list[str],
    source_quality: dict[str, object],
    confidence: float,
    transformations: list[str] | None = None,
    policy_context: dict[str, object] | None = None,
    recommendation_rationale: str = "",
    lineage: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "packet_type": packet_type,
        "evidence_refs": list(evidence_refs),
        "source_quality": dict(source_quality),
        "confidence": round(max(0.0, min(1.0, float(confidence))), 4),
        "transformations": list(transformations or []),
        "policy_context": dict(policy_context or {}),
        "recommendation_rationale": recommendation_rationale,
        "lineage": list(lineage or []),
    }
