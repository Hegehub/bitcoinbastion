from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.bastion_trace import TraceReport
from app.db.models.onchain import OnchainEvent
from app.db.repositories.bastion_trace_repository import BastionTraceRepository
from app.schemas.bastion_trace import TraceBand, TraceScoringInput
from app.services.bastion_trace.claims.collector import TraceClaimCollector
from app.services.bastion_trace.claims.domain import (
    BitcoinNetworkClaimValue,
    TraceClaimPredicate,
    TraceClaimProducerStatus,
    TraceClaimValueKind,
)
from app.services.bastion_trace.claims.persistence import TraceClaimRepository
from app.services.bastion_trace.claims.producers import (
    AddressSyntaxNetworkClaimProducer,
    BaselineRiskBandClaimProducer,
    ObservationNetworkClaimProducer,
    TraceClaimProductionContext,
)
from app.services.bastion_trace.scoring import score_trace
from app.services.bastion_trace.trace_service import TraceService
from app.services.bitcoin_observations.producer import BitcoinObservationProducer


ADDRESS = "bc1qexampleaddress0000000000000000000000000"
NOW = datetime(2026, 8, 15, tzinfo=UTC)


def _event(network: str = "bitcoin-mainnet") -> OnchainEvent:
    return OnchainEvent(
        id=1,
        event_type="large_transfer",
        txid="aa11",
        address=ADDRESS,
        value_sats=10_000,
        fee_sats=100,
        block_height=900_001,
        observed_at=NOW,
        provider="bitcoin_core_rpc",
        raw_payload_json=(
            '{"provider":"bitcoin_core_rpc","source_type":"rpc",'
            f'"network":"{network}"}}'
        ),
        confidence_score=0.8,
    )


def _context(*, observations=()):
    return TraceClaimProductionContext(
        capture_id="trace_report:1",
        address=ADDRESS,
        evaluated_at=NOW,
        scoring=score_trace(TraceScoringInput(baseline_mode=True)),
        observations=observations,
    )


def test_two_independent_producers_emit_comparable_agreeing_network_claims() -> None:
    observations = BitcoinObservationProducer().from_onchain_event(_event()).observations
    collection = TraceClaimCollector().collect(_context(observations=observations))
    network_claims = tuple(
        claim
        for claim in collection.claims
        if claim.predicate is TraceClaimPredicate.BITCOIN_NETWORK
    )
    assert len(network_claims) == 2
    assert {claim.producer_id for claim in network_claims} == {
        "bitcoin-address-syntax-network",
        "bitcoin-observation-source-network",
    }
    assert {claim.value.network for claim in network_claims} == {"bitcoin-mainnet"}  # type: ignore[union-attr]
    assert len({claim.id for claim in network_claims}) == 2


def test_baseline_risk_claim_preserves_existing_scoring_semantics() -> None:
    scoring = score_trace(TraceScoringInput(baseline_mode=True))
    result = BaselineRiskBandClaimProducer().produce(replace(_context(), scoring=scoring))
    assert result.status is TraceClaimProducerStatus.SUCCESS_WITH_CLAIM
    assert result.claims[0].value.band is scoring.band  # type: ignore[union-attr]
    assert result.claims[0].confidence == scoring.confidence
    assert result.claims[0].limitations == ("baseline_scoring_only",)


def test_source_unavailable_and_unsupported_are_not_claims() -> None:
    unavailable = ObservationNetworkClaimProducer().produce(_context())
    assert unavailable.status is TraceClaimProducerStatus.SOURCE_UNAVAILABLE
    assert unavailable.claims == ()
    unsupported = AddressSyntaxNetworkClaimProducer().produce(
        replace(_context(), address="unsupported")
    )
    assert unsupported.status is TraceClaimProducerStatus.NO_APPLICABLE_CLAIM
    assert unsupported.claims == ()


def test_collector_preserves_valid_claim_when_another_producer_fails() -> None:
    class FailingProducer:
        producer_id = "failing-producer"

        def produce(self, context):  # type: ignore[no-untyped-def]
            raise RuntimeError("synthetic producer boundary failure")

    collection = TraceClaimCollector(
        (FailingProducer(), AddressSyntaxNetworkClaimProducer())
    ).collect(_context())
    assert len(collection.claims) == 1
    statuses = {result.producer_id: result.status for result in collection.producer_results}
    assert statuses["failing-producer"] is TraceClaimProducerStatus.PRODUCER_FAILURE
    assert statuses["bitcoin-address-syntax-network"] is TraceClaimProducerStatus.SUCCESS_WITH_CLAIM


def test_claim_identity_determinism_immutability_and_value_validation() -> None:
    first = AddressSyntaxNetworkClaimProducer().produce(_context()).claims[0]
    second = AddressSyntaxNetworkClaimProducer().produce(_context()).claims[0]
    assert first.id == second.id
    with pytest.raises(FrozenInstanceError):
        first.source_id = "other"  # type: ignore[misc]
    with pytest.raises(ValueError):
        replace(
            first,
            predicate=TraceClaimPredicate.RISK_BAND,
            value=BitcoinNetworkClaimValue(
                TraceClaimValueKind.BITCOIN_NETWORK, "bitcoin-mainnet"
            ),
        )


def test_claim_persistence_is_idempotent_and_capture_b_does_not_mutate_a() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        report_a = TraceReport(address=ADDRESS, created_at=NOW)
        session.add(report_a)
        session.commit()
        claims_a = TraceClaimCollector().collect(
            _context(
                observations=BitcoinObservationProducer().from_onchain_event(_event()).observations
            )
        ).claims
        repository = TraceClaimRepository(session)
        repository.add_claims(report_a.id, claims_a)
        repository.add_claims(report_a.id, claims_a)
        persisted_a = repository.list_for_report(report_a.id)
        assert len(persisted_a) == len(claims_a)
        loaded_a = repository.load_claims_for_report(report_a.id)
        assert [claim.id for claim in loaded_a] == [row.id for row in persisted_a]

        report_b = TraceReport(address=ADDRESS, created_at=NOW)
        session.add(report_b)
        session.commit()
        context_b = replace(_context(), capture_id=f"trace_report:{report_b.id}")
        repository.add_claims(report_b.id, TraceClaimCollector().collect(context_b).claims)
        assert repository.list_for_report(report_a.id) == persisted_a


def test_placeholder_unknown_origin_is_not_a_claim_predicate() -> None:
    assert {item.value for item in TraceClaimPredicate} == {"risk_band", "bitcoin_network"}
    assert TraceBand.UNKNOWN.value == "UNKNOWN"


def test_trace_production_persists_two_comparable_network_claim_sources() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(_event())
        session.commit()
        report = TraceService(BastionTraceRepository(session)).analyze_address(ADDRESS)
        assert report.id is not None
        rows = TraceClaimRepository(session).list_for_report(report.id)
        network_rows = [row for row in rows if row.predicate == "bitcoin_network"]
        assert len(network_rows) == 2
        assert {row.producer_id for row in network_rows} == {
            "bitcoin-address-syntax-network",
            "bitcoin-observation-source-network",
        }
        assert {row.value_text for row in network_rows} == {"bitcoin-mainnet"}
