from __future__ import annotations

import json
from datetime import UTC, datetime

from app.integrations.bitcoin.provider import ChainEvent
from app.services.blockchain.chain_state_service import ChainStateService
from app.services.citadel.citadel_assessment_service import CitadelAssessmentService
from app.services.citadel.policy_maturity_service import CitadelPolicyService
from app.services.scoring.onchain_scoring import OnchainScoringService
from app.services.treasury.treasury_service import TreasuryService
from tests.unit.test_treasury_policy_workflow import FakeRepo, _policy_result
from app.schemas.treasury import TreasuryRequestIn


def test_chain_state_explainability_contract_fields_exist() -> None:
    out = ChainStateService().evaluate(
        tip_height=100,
        observed_block_height=99,
        provider_tip_height=100,
        provider_confidence=0.8,
        provider_data_age_seconds=15,
        data_source="provider_probe",
    )
    contract = out.explainability["contract"]
    for key in [
        "version",
        "domain",
        "source_type",
        "provider_name",
        "is_mock",
        "is_fallback",
        "confidence",
        "freshness",
        "limitations",
        "signals",
    ]:
        assert key in contract


def test_evidence_chain_survives_protocol_to_citadel_transformations() -> None:
    out = CitadelAssessmentService().build_assessment(owner_type="user", owner_id=501)
    explainability = out.explainability.model_dump()
    chain = explainability["evidence_chain"]
    assert len(chain) >= 5
    assert [item["domain"] for item in chain[:5]] == [
        "protocol",
        "scoring",
        "policy",
        "citadel",
        "recommendation",
    ]
    packets = explainability["audit_packets"]
    assert packets
    assert packets[0]["lineage"]


def test_fallback_markers_and_confidence_propagate_to_signal_audit_packet() -> None:
    event = ChainEvent(
        event_type="large_transfer",
        txid="fallback-1",
        address="bc1qfallback",
        value_sats=2_000_000_000,
        block_height=100,
        observed_at=datetime.now(UTC),
        payload={"source_type": "provider"},
    )
    fresh = ChainStateService().evaluate(
        tip_height=101,
        observed_block_height=100,
        data_source="provider_probe",
        provider_data_age_seconds=10,
    )
    stale_fallback = ChainStateService().evaluate(
        tip_height=101,
        observed_block_height=100,
        data_source="provider_fallback",
        provider_data_age_seconds=1200,
    )

    fresh_score = OnchainScoringService().score(event, chain_state=fresh)
    fallback_score = OnchainScoringService().score(event, chain_state=stale_fallback)

    assert fallback_score.confidence < fresh_score.confidence
    packet = fallback_score.explainability["audit_packet"]
    assert packet["source_quality"]["is_fallback"] is True
    assert packet["source_quality"]["freshness"]["provider_freshness_band"] == "very_stale"


def test_policy_and_treasury_audit_packets_are_serializable_and_complete() -> None:
    policy = CitadelPolicyService().evaluate(owner_id=40, wallet_health_score=None, has_recent_health_report=False)
    policy_packet = policy["explainability"]["audit_packet"]
    assert policy_packet["packet_type"] in {"policy_violation", "policy_review"}
    assert isinstance(json.dumps(policy_packet), str)

    service = TreasuryService(FakeRepo())
    service.policy_service.evaluate_and_log = lambda db, payload: _policy_result(False)  # type: ignore[method-assign]
    created = service.create_request(
        TreasuryRequestIn(
            title="Regression treasury",
            amount_sats=12_000_000,
            destination_reference="vault-x",
            wallet_health_score=40,
        ),
        requested_by=7,
    )
    snapshot = json.loads(created.policy_snapshot_json)
    treasury_packet = snapshot["audit_packet"]
    for key in [
        "packet_type",
        "evidence_refs",
        "source_quality",
        "confidence",
        "transformations",
        "policy_context",
        "recommendation_rationale",
        "lineage",
    ]:
        assert key in treasury_packet
    assert isinstance(json.dumps(treasury_packet), str)


def test_citadel_protocol_quality_degrades_with_stale_fallback_context() -> None:
    service = CitadelAssessmentService()
    strong = service.build_assessment(
        owner_type="user",
        owner_id=601,
        wallet_context=service.build_wallet_context(
            chain_data_source="provider_probe",
            chain_provider_data_age_seconds=10,
            chain_tip_height=100,
            chain_observed_height=99,
            chain_headers_height=100,
        ),
    )
    weak = service.build_assessment(
        owner_type="user",
        owner_id=602,
        wallet_context=service.build_wallet_context(
            chain_data_source="provider_fallback",
            chain_provider_data_age_seconds=1800,
            chain_tip_height=100,
            chain_observed_height=99,
            chain_headers_height=102,
        ),
    )

    strong_q = strong.explainability.model_dump()["protocol_input_quality"]
    weak_q = weak.explainability.model_dump()["protocol_input_quality"]

    assert weak_q["confidence"] <= strong_q["confidence"]
    assert weak_q["freshness"]["provider_freshness_band"] in {"stale", "very_stale", "unknown"}
    assert weak_q["raw_confidence"] >= weak_q["confidence"]
