from dataclasses import replace
from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.bastion_trace import TraceReport
from app.db.models.onchain import OnchainEvent
from app.schemas.bastion_trace import TraceScoringInput
from app.services.bastion_trace.claims.collector import TraceClaimCollector
from app.services.bastion_trace.claims.domain import (
    TraceClaimPredicate,
    TraceClaimProducerResult,
    TraceClaimProducerStatus,
    TraceClaimSubject,
    TraceClaimSubjectKind,
    stable_claim_subject_id,
)
from app.services.bastion_trace.claims.persistence import TraceClaimRepository
from app.services.bastion_trace.claims.producers import TraceClaimProductionContext
from app.services.bastion_trace.disagreement.domain import (
    DISAGREEMENT_EVALUATOR_VERSION,
    TraceDisagreementStatus,
    TraceResolutionStatus,
)
from app.services.bastion_trace.disagreement.evaluator import TraceDisagreementEvaluator
from app.services.bastion_trace.disagreement.history import TraceHistoricalDisagreementService
from app.services.bastion_trace.scoring import score_trace
from app.services.bitcoin_observations.producer import BitcoinObservationProducer

ADDRESS = "bc1qexampleaddress0000000000000000000000000"
NOW = datetime(2026, 8, 15, tzinfo=UTC)


def _event(network: str) -> OnchainEvent:
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


def _collection(network: str, capture_id: str = "trace_report:1"):
    observations = BitcoinObservationProducer().from_onchain_event(
        _event(network)
    ).observations
    return TraceClaimCollector().collect(
        TraceClaimProductionContext(
            capture_id=capture_id,
            address=ADDRESS,
            evaluated_at=NOW,
            scoring=score_trace(TraceScoringInput(baseline_mode=True)),
            observations=observations,
        )
    )


def _network_claims(network: str, capture_id: str = "trace_report:1"):
    return tuple(
        claim
        for claim in _collection(network, capture_id).claims
        if claim.predicate is TraceClaimPredicate.BITCOIN_NETWORK
    )


def test_real_d1_producers_agree_with_source_attribution() -> None:
    claims = _network_claims("bitcoin-mainnet")
    result = TraceDisagreementEvaluator().evaluate(claims)
    assert result.status is TraceDisagreementStatus.AGREEMENT
    assert result.evaluator_version == DISAGREEMENT_EVALUATOR_VERSION
    assert result.claim_set is not None
    assert len(result.claim_set.claims) == 2
    assert {claim.producer_id for claim in result.participating_claims} == {
        "bitcoin-address-syntax-network",
        "bitcoin-observation-source-network",
    }
    assert result.canonical_claim_id is None
    assert result.resolution_status is TraceResolutionStatus.NOT_APPLICABLE


def test_valid_real_producer_outputs_can_be_unresolved_disagreement() -> None:
    claims = _network_claims("bitcoin-testnet")
    result = TraceDisagreementEvaluator().evaluate(claims)
    assert result.status is TraceDisagreementStatus.DISAGREEMENT
    assert result.resolution_status is TraceResolutionStatus.UNRESOLVED
    assert result.canonical_claim_id is None
    assert {claim.value.network for claim in result.participating_claims} == {  # type: ignore[union-attr]
        "bitcoin-mainnet",
        "bitcoin-testnet",
    }


def test_source_unavailable_failure_and_insufficient_data_are_not_disagreement() -> None:
    claim = _network_claims("bitcoin-mainnet")[0]
    for status in (
        TraceClaimProducerStatus.SOURCE_UNAVAILABLE,
        TraceClaimProducerStatus.PRODUCER_FAILURE,
        TraceClaimProducerStatus.INSUFFICIENT_DATA,
    ):
        producer_result = TraceClaimProducerResult("other", status)
        result = TraceDisagreementEvaluator().evaluate((claim,), (producer_result,))
        assert result.status is TraceDisagreementStatus.INSUFFICIENT_COMPARABLE_CLAIMS
        assert result.status is not TraceDisagreementStatus.DISAGREEMENT
        assert (
            result.coverage.unavailable_producer_count
            + result.coverage.failed_producer_count
            + result.coverage.insufficient_producer_count
            == 1
        )


def test_mixed_predicates_subjects_and_capture_boundaries_are_not_comparable() -> None:
    collection = _collection("bitcoin-mainnet")
    network_claim = _network_claims("bitcoin-mainnet")[0]
    risk_claim = next(
        claim for claim in collection.claims if claim.predicate is TraceClaimPredicate.RISK_BAND
    )
    assert TraceDisagreementEvaluator().evaluate(
        (network_claim, risk_claim)
    ).status is TraceDisagreementStatus.NOT_COMPARABLE

    other_subject = TraceClaimSubject(
        TraceClaimSubjectKind.BITCOIN_ADDRESS,
        stable_claim_subject_id(TraceClaimSubjectKind.BITCOIN_ADDRESS, "bc1qother"),
        "bc1qother",
    )
    assert TraceDisagreementEvaluator().evaluate(
        (network_claim, replace(_network_claims("bitcoin-mainnet")[1], subject=other_subject))
    ).status is TraceDisagreementStatus.NOT_COMPARABLE
    assert TraceDisagreementEvaluator().evaluate(
        (network_claim, replace(_network_claims("bitcoin-mainnet")[1], capture_id="trace_report:2"))
    ).status is TraceDisagreementStatus.NOT_COMPARABLE


def test_order_and_duplicate_claims_do_not_change_or_fabricate_result() -> None:
    claims = _network_claims("bitcoin-mainnet")
    first = TraceDisagreementEvaluator().evaluate(claims)
    second = TraceDisagreementEvaluator().evaluate(tuple(reversed(claims)))
    assert first.id == second.id
    assert first.status is second.status
    duplicate = TraceDisagreementEvaluator().evaluate((claims[0], claims[0]))
    assert duplicate.status is TraceDisagreementStatus.INSUFFICIENT_COMPARABLE_CLAIMS
    main_observation_claim = next(
        claim
        for claim in _network_claims("bitcoin-mainnet")
        if claim.producer_id == "bitcoin-observation-source-network"
    )
    test_observation_claim = next(
        claim
        for claim in _network_claims("bitcoin-testnet")
        if claim.producer_id == "bitcoin-observation-source-network"
    )
    assert TraceDisagreementEvaluator().evaluate(
        (main_observation_claim, test_observation_claim)
    ).status is TraceDisagreementStatus.NOT_COMPARABLE


def test_historical_report_a_is_unchanged_after_conflicting_report_b() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        report_a = TraceReport(address=ADDRESS, created_at=NOW)
        report_b = TraceReport(address=ADDRESS, created_at=NOW)
        session.add_all((report_a, report_b))
        session.commit()
        repository = TraceClaimRepository(session)
        claims_a = _collection("bitcoin-mainnet", f"trace_report:{report_a.id}").claims
        repository.add_claims(report_a.id, claims_a)
        historical = TraceHistoricalDisagreementService(session)
        result_a_before = historical.for_report(report_a.id)

        claims_b = _collection("bitcoin-testnet", f"trace_report:{report_b.id}").claims
        repository.add_claims(report_b.id, claims_b)
        result_a_after = historical.for_report(report_a.id)
        result_b = historical.for_report(report_b.id)

        assert result_a_before == result_a_after
        assert any(item.status is TraceDisagreementStatus.AGREEMENT for item in result_a_after)
        assert any(item.status is TraceDisagreementStatus.DISAGREEMENT for item in result_b)
        loaded_a = repository.load_claims_for_report(report_a.id)
        assert {claim.producer_version for claim in loaded_a} >= {
            "bitcoin-address-syntax-v1",
            "bitcoin-observation-network-v1",
        }
