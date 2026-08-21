from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from prometheus_client import Counter, Histogram

from app.services.bastion_trace.claims.domain import (
    TraceClaim,
    TraceClaimProducerResult,
    TraceClaimProducerStatus,
)
from app.services.bastion_trace.claims.producers import (
    AddressSyntaxNetworkClaimProducer,
    BaselineRiskBandClaimProducer,
    ObservationNetworkClaimProducer,
    TraceClaimProducer,
    TraceClaimProductionContext,
)

TRACE_CLAIM_PRODUCER_EXECUTIONS = Counter(
    "bastion_trace_claim_producer_executions_total",
    "Trace Claim producer outcomes",
    ("producer", "status"),
)
TRACE_CLAIM_PRODUCER_DURATION = Histogram(
    "bastion_trace_claim_producer_duration_seconds",
    "Trace Claim producer execution duration",
    ("producer",),
)


@dataclass(frozen=True, slots=True)
class TraceClaimCollection:
    claims: tuple[TraceClaim, ...]
    producer_results: tuple[TraceClaimProducerResult, ...]


class TraceClaimCollector:
    """Collects attributable Claims; it deliberately does not evaluate disagreement."""

    def __init__(self, producers: tuple[TraceClaimProducer, ...] | None = None) -> None:
        self._producers = producers or (
            AddressSyntaxNetworkClaimProducer(),
            BaselineRiskBandClaimProducer(),
            ObservationNetworkClaimProducer(),
        )

    def collect(self, context: TraceClaimProductionContext) -> TraceClaimCollection:
        results = tuple(
            self._invoke(producer, context)
            for producer in sorted(self._producers, key=lambda item: item.producer_id)
        )
        claims = {
            claim.id: claim
            for result in results
            for claim in result.claims
        }
        return TraceClaimCollection(
            claims=tuple(claims[key] for key in sorted(claims)),
            producer_results=results,
        )

    def _invoke(
        self,
        producer: TraceClaimProducer,
        context: TraceClaimProductionContext,
    ) -> TraceClaimProducerResult:
        started = perf_counter()
        try:
            result = producer.produce(context)
        except Exception:
            result = TraceClaimProducerResult(
                producer.producer_id,
                TraceClaimProducerStatus.PRODUCER_FAILURE,
                limitation="claim_producer_failed",
            )
        TRACE_CLAIM_PRODUCER_DURATION.labels(producer=producer.producer_id).observe(
            perf_counter() - started
        )
        TRACE_CLAIM_PRODUCER_EXECUTIONS.labels(
            producer=producer.producer_id,
            status=result.status.value,
        ).inc()
        return result
