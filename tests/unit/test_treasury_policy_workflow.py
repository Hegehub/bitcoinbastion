import json
from datetime import UTC, datetime

from app.schemas.policy import PolicyCheckResponse, PolicyRuleOut
from app.schemas.treasury import TreasuryRequestIn, TreasuryRequestOut
from app.services.treasury.treasury_service import TreasuryService


class FakeRepo:
    def __init__(self) -> None:
        self.db = object()

    def create(self, item):  # noqa: ANN001
        item.id = 1
        item.created_at = datetime.now(UTC)
        return item


def _policy_result(allowed: bool) -> PolicyCheckResponse:
    return PolicyCheckResponse(
        allowed=allowed,
        violations=[] if allowed else ["Wallet health is below minimum threshold (60)."],
        next_actions=["Proceed"] if allowed else ["Escalate to treasury operator review."],
        evaluated_policy="default",
        applied_rules=[PolicyRuleOut(rule_key="min_wallet_health_score", rule_value="60", severity="error")],
    )


def test_treasury_request_uses_pending_status_when_policy_allows() -> None:
    service = TreasuryService(FakeRepo())
    service.policy_service.evaluate_and_log = lambda db, payload: _policy_result(True)  # type: ignore[method-assign]

    created = service.create_request(
        TreasuryRequestIn(title="Cold storage rebalance", amount_sats=100_000, destination_reference="vault-01"),
        requested_by=7,
    )

    assert created.status == "pending"
    assert created.required_approvals == 1
    snapshot = json.loads(created.policy_snapshot_json)
    assert snapshot["allowed"] is True


def test_treasury_request_escalates_when_policy_denies() -> None:
    service = TreasuryService(FakeRepo())
    service.policy_service.evaluate_and_log = lambda db, payload: _policy_result(False)  # type: ignore[method-assign]

    created = service.create_request(
        TreasuryRequestIn(
            title="Large outgoing transfer",
            amount_sats=20_000_000,
            destination_reference="otc-desk-ref",
            wallet_health_score=40,
        ),
        requested_by=8,
    )

    assert created.status == "needs_review"
    assert created.required_approvals == 2

    out = TreasuryRequestOut.from_model_with_policy(created)
    assert out.policy_allowed is False
    assert out.policy_violations


def test_treasury_request_adds_chain_state_warning_when_reorg_risk_high(monkeypatch) -> None:
    service = TreasuryService(FakeRepo())
    service.policy_service.evaluate_and_log = lambda db, payload: _policy_result(True)  # type: ignore[method-assign]
    monkeypatch.setattr(
        TreasuryService,
        "_chain_state_for_treasury",
        staticmethod(lambda **kwargs: __import__("app.services.blockchain.chain_state_service", fromlist=["ChainStateService"]).ChainStateService().evaluate(
            tip_height=900_000, observed_block_height=900_000, headers_height=900_003, data_source="repository_fallback"
        )),
    )

    created = service.create_request(
        TreasuryRequestIn(title="Emergency spend", amount_sats=12_000_000, destination_reference="vault-hot", wallet_health_score=45),
        requested_by=9,
    )
    snapshot = json.loads(created.policy_snapshot_json)
    assert created.status == "needs_review"
    assert snapshot["chain_state_context"]["warnings"]
    assert snapshot["audit_packet"]["packet_type"] in {"treasury_warning", "treasury_review"}
    assert snapshot["audit_packet"]["evidence_refs"]
