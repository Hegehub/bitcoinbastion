from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib

from app.services.bastion_trace.claims.domain import (
    TraceClaim,
    TraceClaimPredicate,
    TraceClaimProducerResult,
    TraceClaimSubject,
)

DISAGREEMENT_EVALUATOR_VERSION = "trace-disagreement-evaluator-v1"


class TraceDisagreementStatus(str, Enum):
    AGREEMENT = "agreement"
    DISAGREEMENT = "disagreement"
    INSUFFICIENT_COMPARABLE_CLAIMS = "insufficient_comparable_claims"
    NOT_COMPARABLE = "not_comparable"


class TraceResolutionStatus(str, Enum):
    UNRESOLVED = "unresolved"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class TraceClaimSet:
    id: str
    capture_id: str
    subject: TraceClaimSubject
    predicate: TraceClaimPredicate
    claims: tuple[TraceClaim, ...]
    evaluated_at: datetime
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TraceDisagreementCoverage:
    eligible_claim_count: int
    eligible_producer_count: int
    unavailable_producer_count: int
    insufficient_producer_count: int
    failed_producer_count: int


@dataclass(frozen=True, slots=True)
class TraceDisagreementEvaluation:
    id: str
    evaluator_version: str
    status: TraceDisagreementStatus
    resolution_status: TraceResolutionStatus
    claim_set: TraceClaimSet | None
    participating_claims: tuple[TraceClaim, ...]
    canonical_claim_id: None
    coverage: TraceDisagreementCoverage
    evaluated_at: datetime
    limitations: tuple[str, ...] = ()


def stable_claim_set_id(
    capture_id: str,
    subject_id: str,
    predicate: TraceClaimPredicate,
    claim_ids: tuple[str, ...],
) -> str:
    return _stable_id(
        "trace_claim_set", capture_id, subject_id, predicate.value, *sorted(claim_ids)
    )


def stable_evaluation_id(
    status: TraceDisagreementStatus,
    claim_ids: tuple[str, ...],
    capture_id: str,
) -> str:
    return _stable_id(
        "trace_disagreement",
        DISAGREEMENT_EVALUATOR_VERSION,
        capture_id,
        status.value,
        *sorted(claim_ids),
    )


def coverage_from_results(
    eligible_claims: tuple[TraceClaim, ...],
    producer_results: tuple[TraceClaimProducerResult, ...],
) -> TraceDisagreementCoverage:
    from app.services.bastion_trace.claims.domain import TraceClaimProducerStatus

    statuses = tuple(result.status for result in producer_results)
    return TraceDisagreementCoverage(
        eligible_claim_count=len(eligible_claims),
        eligible_producer_count=len({claim.producer_id for claim in eligible_claims}),
        unavailable_producer_count=statuses.count(TraceClaimProducerStatus.SOURCE_UNAVAILABLE),
        insufficient_producer_count=statuses.count(TraceClaimProducerStatus.INSUFFICIENT_DATA),
        failed_producer_count=statuses.count(TraceClaimProducerStatus.PRODUCER_FAILURE),
    )


def _stable_id(namespace: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join((namespace, *parts)).encode()).hexdigest()[:24]
    return f"{namespace}:{digest}"
