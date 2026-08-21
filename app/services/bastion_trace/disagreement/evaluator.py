from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter

from prometheus_client import Counter, Histogram

from app.services.bastion_trace.claims.domain import TraceClaim, TraceClaimProducerResult
from app.services.bastion_trace.disagreement.comparators import (
    COMPARATORS,
    TraceComparisonOutcome,
)
from app.services.bastion_trace.disagreement.domain import (
    DISAGREEMENT_EVALUATOR_VERSION,
    TraceClaimSet,
    TraceDisagreementEvaluation,
    TraceDisagreementStatus,
    TraceResolutionStatus,
    coverage_from_results,
    stable_claim_set_id,
    stable_evaluation_id,
)

TRACE_DISAGREEMENT_EVALUATIONS = Counter(
    "bastion_trace_disagreement_evaluations_total",
    "Trace disagreement evaluation outcomes",
    ("status",),
)
TRACE_DISAGREEMENT_DURATION = Histogram(
    "bastion_trace_disagreement_evaluation_duration_seconds",
    "Trace disagreement evaluation duration",
)


class TraceDisagreementEvaluator:
    """Deterministically evaluates reviewed comparable Claim domains."""

    def evaluate(
        self,
        claims: tuple[TraceClaim, ...],
        producer_results: tuple[TraceClaimProducerResult, ...] = (),
    ) -> TraceDisagreementEvaluation:
        started = perf_counter()
        ordered = tuple(sorted({claim.id: claim for claim in claims}.values(), key=lambda c: c.id))
        status, claim_set, limitations = self._evaluate_ordered(ordered)
        capture_id = claim_set.capture_id if claim_set is not None else self._capture_id(ordered)
        evaluated_at = (
            claim_set.evaluated_at
            if claim_set is not None
            else max((claim.evaluated_at for claim in ordered), default=datetime.now(UTC))
        )
        coverage = coverage_from_results(ordered, producer_results)
        result = TraceDisagreementEvaluation(
            id=stable_evaluation_id(status, tuple(claim.id for claim in ordered), capture_id),
            evaluator_version=DISAGREEMENT_EVALUATOR_VERSION,
            status=status,
            resolution_status=(
                TraceResolutionStatus.UNRESOLVED
                if status is TraceDisagreementStatus.DISAGREEMENT
                else TraceResolutionStatus.NOT_APPLICABLE
            ),
            claim_set=claim_set,
            participating_claims=ordered,
            canonical_claim_id=None,
            coverage=coverage,
            evaluated_at=evaluated_at,
            limitations=limitations,
        )
        TRACE_DISAGREEMENT_EVALUATIONS.labels(status=status.value).inc()
        TRACE_DISAGREEMENT_DURATION.observe(perf_counter() - started)
        return result

    def _evaluate_ordered(
        self, claims: tuple[TraceClaim, ...]
    ) -> tuple[TraceDisagreementStatus, TraceClaimSet | None, tuple[str, ...]]:
        if not claims:
            return (
                TraceDisagreementStatus.INSUFFICIENT_COMPARABLE_CLAIMS,
                None,
                ("no_eligible_claims",),
            )
        subjects = {claim.subject.object_id for claim in claims}
        predicates = {claim.predicate for claim in claims}
        captures = {claim.capture_id for claim in claims}
        if len(subjects) != 1 or len(predicates) != 1 or len(captures) != 1:
            return TraceDisagreementStatus.NOT_COMPARABLE, None, ("mixed_claim_context",)
        predicate = claims[0].predicate
        comparator = COMPARATORS.get(predicate)
        if comparator is None:
            return TraceDisagreementStatus.NOT_COMPARABLE, None, ("unsupported_predicate",)
        producer_counts: dict[str, int] = {}
        for claim in claims:
            producer_counts[claim.producer_id] = producer_counts.get(claim.producer_id, 0) + 1
        if any(count > 1 for count in producer_counts.values()):
            return (
                TraceDisagreementStatus.NOT_COMPARABLE,
                None,
                ("multiple_distinct_claims_from_same_producer",),
            )
        independent_claims = self._independent_claims(claims)
        claim_set = TraceClaimSet(
            id=stable_claim_set_id(
                claims[0].capture_id,
                claims[0].subject.object_id,
                predicate,
                tuple(claim.id for claim in independent_claims),
            ),
            capture_id=claims[0].capture_id,
            subject=claims[0].subject,
            predicate=predicate,
            claims=independent_claims,
            evaluated_at=max(claim.evaluated_at for claim in independent_claims),
        )
        if len(independent_claims) < 2:
            return (
                TraceDisagreementStatus.INSUFFICIENT_COMPARABLE_CLAIMS,
                claim_set,
                ("fewer_than_two_independent_claims",),
            )
        outcome = comparator.compare(independent_claims)
        if outcome is TraceComparisonOutcome.AGREEMENT:
            return TraceDisagreementStatus.AGREEMENT, claim_set, ()
        if outcome is TraceComparisonOutcome.DISAGREEMENT:
            return TraceDisagreementStatus.DISAGREEMENT, claim_set, ()
        return TraceDisagreementStatus.NOT_COMPARABLE, claim_set, ("comparator_rejected_claims",)

    @staticmethod
    def _independent_claims(claims: tuple[TraceClaim, ...]) -> tuple[TraceClaim, ...]:
        by_producer: dict[str, TraceClaim] = {}
        for claim in claims:
            by_producer.setdefault(claim.producer_id, claim)
        return tuple(sorted(by_producer.values(), key=lambda claim: claim.id))

    @staticmethod
    def _capture_id(claims: tuple[TraceClaim, ...]) -> str:
        captures = {claim.capture_id for claim in claims}
        return next(iter(captures)) if len(captures) == 1 else "incompatible_capture"
