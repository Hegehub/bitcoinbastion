from datetime import UTC, datetime

from app.schemas.bastion_trace import OriginPassport, ProviderDisagreementResult, EvidenceIndependenceResult


def build_origin_passport(address: str, evidence_refs: list[str], disagreement: ProviderDisagreementResult, independence: EvidenceIndependenceResult) -> OriginPassport:
    low_conf = 0.2 if not evidence_refs else 0.4
    return OriginPassport(
        address=address,
        chain="bitcoin",
        origin_category="unknown" if not evidence_refs else "self_custody",
        origin_label="Unknown origin" if not evidence_refs else "Possible self-custody association",
        origin_confidence=low_conf,
        first_seen_at=None,
        last_seen_at=None,
        source_count=independence.source_count,
        independent_source_count=independence.independent_source_count,
        evidence_refs=evidence_refs,
        limitations=["origin_source_limited"] if not evidence_refs else ["source_limited_assessment"],
        reason_codes=["ORIGIN_SOURCE_LIMITED", "ORIGIN_PASSPORT_CREATED"] if not evidence_refs else ["ORIGIN_PASSPORT_CREATED"],
        provider_disagreement=disagreement,
        evidence_independence_score=independence.score,
        advisory_not_legal_verdict=True,
        not_consensus_proof=True,
        no_custody=True,
        created_at=datetime.now(UTC),
    )
