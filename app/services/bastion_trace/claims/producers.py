from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.schemas.bastion_trace import TraceScoringResult
from app.services.bastion_trace.claims.domain import (
    CLAIM_SCHEMA_VERSION,
    BitcoinNetworkClaimValue,
    RiskBandClaimValue,
    TraceClaim,
    TraceClaimPredicate,
    TraceClaimProducerResult,
    TraceClaimProducerStatus,
    TraceClaimProvenance,
    TraceClaimSubject,
    TraceClaimSubjectKind,
    TraceClaimValueKind,
    stable_claim_id,
    stable_claim_subject_id,
)
from app.services.bitcoin_observations.domain import AddressObserved, BitcoinObservation


@dataclass(frozen=True, slots=True)
class TraceClaimProductionContext:
    capture_id: str
    address: str
    evaluated_at: datetime
    scoring: TraceScoringResult | None = None
    observations: tuple[BitcoinObservation, ...] = ()


class TraceClaimProducer(Protocol):
    producer_id: str

    def produce(self, context: TraceClaimProductionContext) -> TraceClaimProducerResult: ...


class BaselineRiskBandClaimProducer:
    producer_id = "trace-baseline-risk-band"
    producer_version = "baseline-trace-v1"

    def produce(self, context: TraceClaimProductionContext) -> TraceClaimProducerResult:
        if context.scoring is None:
            return TraceClaimProducerResult(
                self.producer_id,
                TraceClaimProducerStatus.INSUFFICIENT_DATA,
                limitation="baseline_scoring_result_unavailable",
            )
        subject = _address_subject(context.address)
        value = RiskBandClaimValue(TraceClaimValueKind.RISK_BAND, context.scoring.band)
        claim = _claim(
            context=context,
            subject=subject,
            predicate=TraceClaimPredicate.RISK_BAND,
            value=value,
            producer_id=self.producer_id,
            producer_version=self.producer_version,
            source_id="baseline_internal_rules",
            input_references=(f"trace_scoring:{context.capture_id}",),
            limitations=("baseline_scoring_only",),
            confidence=context.scoring.confidence,
        )
        return TraceClaimProducerResult(
            self.producer_id, TraceClaimProducerStatus.SUCCESS_WITH_CLAIM, (claim,)
        )


class AddressSyntaxNetworkClaimProducer:
    producer_id = "bitcoin-address-syntax-network"
    producer_version = "bitcoin-address-syntax-v1"

    def produce(self, context: TraceClaimProductionContext) -> TraceClaimProducerResult:
        network = _network_from_address(context.address)
        if network is None:
            return TraceClaimProducerResult(
                self.producer_id,
                TraceClaimProducerStatus.NO_APPLICABLE_CLAIM,
                limitation="address_network_syntax_unsupported",
            )
        subject = _address_subject(context.address)
        value = BitcoinNetworkClaimValue(TraceClaimValueKind.BITCOIN_NETWORK, network)
        claim = _claim(
            context=context,
            subject=subject,
            predicate=TraceClaimPredicate.BITCOIN_NETWORK,
            value=value,
            producer_id=self.producer_id,
            producer_version=self.producer_version,
            source_id="bitcoin_address_encoding",
            input_references=(f"bitcoin_address:{context.address}",),
            limitations=("network_from_address_encoding",),
        )
        return TraceClaimProducerResult(
            self.producer_id, TraceClaimProducerStatus.SUCCESS_WITH_CLAIM, (claim,)
        )


class ObservationNetworkClaimProducer:
    producer_id = "bitcoin-observation-source-network"
    producer_version = "bitcoin-observation-network-v1"

    def produce(self, context: TraceClaimProductionContext) -> TraceClaimProducerResult:
        matching = tuple(
            item
            for item in context.observations
            if isinstance(item, AddressObserved) and item.address == context.address
        )
        if not matching:
            return TraceClaimProducerResult(
                self.producer_id,
                TraceClaimProducerStatus.SOURCE_UNAVAILABLE,
                limitation="address_observation_unavailable",
            )
        subject = _address_subject(context.address)
        claims = tuple(
            _claim(
                context=context,
                subject=subject,
                predicate=TraceClaimPredicate.BITCOIN_NETWORK,
                value=BitcoinNetworkClaimValue(
                    TraceClaimValueKind.BITCOIN_NETWORK, item.provenance.source.network
                ),
                producer_id=self.producer_id,
                producer_version=self.producer_version,
                source_id=item.provenance.source.source_name,
                input_references=(item.id,),
                limitations=tuple(
                    sorted(set(item.provenance.limitations) | {"network_from_source_metadata"})
                ),
            )
            for item in matching
        )
        return TraceClaimProducerResult(
            self.producer_id, TraceClaimProducerStatus.SUCCESS_WITH_CLAIM, claims
        )


def _claim(
    *,
    context: TraceClaimProductionContext,
    subject: TraceClaimSubject,
    predicate: TraceClaimPredicate,
    value: RiskBandClaimValue | BitcoinNetworkClaimValue,
    producer_id: str,
    producer_version: str,
    source_id: str,
    input_references: tuple[str, ...],
    limitations: tuple[str, ...],
    confidence: float | None = None,
) -> TraceClaim:
    provenance = TraceClaimProvenance(input_references, limitations)
    return TraceClaim(
        id=stable_claim_id(
            capture_id=context.capture_id,
            subject_id=subject.object_id,
            predicate=predicate,
            producer_id=producer_id,
            producer_version=producer_version,
            source_id=source_id,
            value=value,
            input_references=input_references,
        ),
        claim_schema_version=CLAIM_SCHEMA_VERSION,
        capture_id=context.capture_id,
        subject=subject,
        predicate=predicate,
        value=value,
        producer_id=producer_id,
        producer_version=producer_version,
        source_id=source_id,
        evaluated_at=context.evaluated_at,
        provenance=provenance,
        confidence=confidence,
        limitations=limitations,
    )


def _address_subject(address: str) -> TraceClaimSubject:
    return TraceClaimSubject(
        TraceClaimSubjectKind.BITCOIN_ADDRESS,
        stable_claim_subject_id(TraceClaimSubjectKind.BITCOIN_ADDRESS, address),
        address,
    )


def _network_from_address(address: str) -> str | None:
    lowered = address.lower()
    if lowered.startswith(("bc1", "1", "3")):
        return "bitcoin-mainnet"
    if lowered.startswith(("tb1", "m", "n", "2")):
        return "bitcoin-testnet"
    return None
