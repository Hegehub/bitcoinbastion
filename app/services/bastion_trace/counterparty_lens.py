from datetime import UTC, datetime

from app.schemas.bastion_trace import CounterpartyLens, CounterpartyRiskLevel, CounterpartyType


def build_counterparty_lens(address: str, trace_band: str, privacy_band: str, origin_category: str, disagreement: str, indep: float) -> CounterpartyLens:
    risk = CounterpartyRiskLevel.UNKNOWN if trace_band == "UNKNOWN" else CounterpartyRiskLevel[trace_band]
    return CounterpartyLens(address=address, chain="bitcoin", counterparty_label="Possible counterparty context", counterparty_type=CounterpartyType.UNKNOWN if origin_category == "unknown" else CounterpartyType.INDIVIDUAL, counterparty_confidence=0.25, trace_band=trace_band, privacy_band=privacy_band, origin_category=origin_category, provider_disagreement_severity=disagreement, evidence_independence_score=indep, counterparty_risk_level=risk, manual_review_recommended=trace_band in {"HIGH", "CRITICAL"}, limitations=["counterparty_identity_not_verified", "counterparty_source_limited"], reason_codes=["COUNTERPARTY_LENS_CREATED", "COUNTERPARTY_IDENTITY_NOT_VERIFIED", "COUNTERPARTY_SOURCE_LIMITED"], operator_guidance=["Possible counterparty context only; identity is not verified."], advisory_not_legal_verdict=True, not_consensus_proof=True, no_custody=True, created_at=datetime.now(UTC))
