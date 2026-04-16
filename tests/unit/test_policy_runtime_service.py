from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models.treasury import PolicyRule, TreasuryPolicy
from app.schemas.policy import PolicyCatalogCompareRequest, PolicyCatalogUpsertIn, PolicyCheckRequest, PolicySimulationRequest
from app.services.policy.policy_service import TreasuryPolicyService


def test_policy_evaluation_and_execution_log_persistence() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    payload = PolicyCheckRequest(
        policy_name="default",
        wallet_health_score=55,
        transaction_amount_sats=20_000_000,
    )

    with Session(engine) as db:
        result = TreasuryPolicyService().evaluate_and_log(db=db, payload=payload)
        rows = TreasuryPolicyService().list_executions(db=db, limit=10, offset=0)
        catalog = TreasuryPolicyService().list_catalog(db=db)

    assert result.allowed is False
    assert len(result.violations) == 2
    assert len(result.applied_rules) >= 2
    assert len(rows) == 1
    assert rows[0].policy_name == "default"
    assert rows[0].allowed is False
    assert catalog[0].name == "default"


def test_policy_rules_override_thresholds() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        policy = TreasuryPolicy(
            name="strict",
            min_wallet_health_score=90,
            max_single_tx_sats=500,
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)

        db.add_all(
            [
                PolicyRule(policy_id=policy.id, rule_key="min_wallet_health_score", rule_value="gte:95", severity="error"),
                PolicyRule(policy_id=policy.id, rule_key="max_single_tx_sats", rule_value="lte:400", severity="error"),
            ]
        )
        db.commit()

        payload = PolicyCheckRequest(policy_name="strict", wallet_health_score=94, transaction_amount_sats=450)
        result = TreasuryPolicyService().evaluate(db=db, payload=payload)

    assert result.allowed is False
    assert any("95" in item for item in result.violations)
    assert any("400" in item for item in result.violations)


def test_policy_catalog_upsert_rewrites_threshold_rules() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        catalog_item = TreasuryPolicyService().upsert_catalog_entry(
            db=db,
            payload=PolicyCatalogUpsertIn(
                name="ops_strict",
                description="Strict policy for high-volatility sessions",
                min_wallet_health_score=88,
                max_single_tx_sats=700_000,
            ),
        )

        payload = PolicyCheckRequest(policy_name="ops_strict", wallet_health_score=87, transaction_amount_sats=800_000)
        result = TreasuryPolicyService().evaluate(db=db, payload=payload)

    assert catalog_item.name == "ops_strict"
    assert catalog_item.min_wallet_health_score == 88
    assert catalog_item.max_single_tx_sats == 700_000
    assert result.allowed is False
    assert any("88" in item for item in result.violations)
    assert any("700000" in item for item in result.violations)


def test_policy_simulation_compare_surfaces_diff() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        service = TreasuryPolicyService()
        service.upsert_catalog_entry(
            db=db,
            payload=PolicyCatalogUpsertIn(
                name="baseline",
                description="baseline profile",
                min_wallet_health_score=60,
                max_single_tx_sats=10_000_000,
            ),
        )
        service.upsert_catalog_entry(
            db=db,
            payload=PolicyCatalogUpsertIn(
                name="strict",
                description="strict profile",
                min_wallet_health_score=90,
                max_single_tx_sats=1_000_000,
            ),
        )

        out = service.simulate_compare(
            db=db,
            payload=PolicySimulationRequest(
                baseline_policy_name="baseline",
                candidate_policy_name="strict",
                wallet_health_score=75,
                transaction_amount_sats=900_000,
                required_approvals=1,
            ),
        )

    assert out.baseline.allowed is True
    assert out.candidate.allowed is False
    assert out.diff.changed is True
    assert out.diff.added_violations
    assert out.diff.changed_rules
    assert out.diff.risk_level == "high"
    assert out.diff.required_approvals_suggested == 2
    assert out.diff.governance_actions


def test_policy_simulation_compare_marks_low_risk_when_unchanged() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        service = TreasuryPolicyService()
        out = service.simulate_compare(
            db=db,
            payload=PolicySimulationRequest(
                baseline_policy_name="default",
                candidate_policy_name="default",
                wallet_health_score=85,
                transaction_amount_sats=200_000,
                required_approvals=1,
            ),
        )

    assert out.diff.risk_level == "low"
    assert out.diff.required_approvals_suggested == 1
    assert out.diff.changed_rules == []


def test_policy_catalog_high_risk_tightening_requires_justification() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        service = TreasuryPolicyService()
        service.upsert_catalog_entry(
            db=db,
            payload=PolicyCatalogUpsertIn(
                name="ops_policy",
                description="baseline",
                min_wallet_health_score=60,
                max_single_tx_sats=10_000_000,
            ),
        )

        try:
            service.upsert_catalog_entry(
                db=db,
                payload=PolicyCatalogUpsertIn(
                    name="ops_policy",
                    description="tightened",
                    min_wallet_health_score=85,
                    max_single_tx_sats=2_000_000,
                ),
            )
            assert False, "Expected ValueError for missing change_justification"
        except ValueError as exc:
            assert "change_justification" in str(exc)

        updated = service.upsert_catalog_entry(
            db=db,
            payload=PolicyCatalogUpsertIn(
                name="ops_policy",
                description="tightened",
                min_wallet_health_score=85,
                max_single_tx_sats=2_000_000,
                change_justification="Volatility spike requires stricter treasury risk posture.",
            ),
        )

    assert updated.min_wallet_health_score == 85
    assert updated.max_single_tx_sats == 2_000_000


def test_policy_catalog_compare_reports_threshold_and_rule_deltas() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        service = TreasuryPolicyService()
        service.upsert_catalog_entry(
            db=db,
            payload=PolicyCatalogUpsertIn(
                name="baseline",
                description="base",
                min_wallet_health_score=60,
                max_single_tx_sats=10_000_000,
            ),
        )
        service.upsert_catalog_entry(
            db=db,
            payload=PolicyCatalogUpsertIn(
                name="candidate",
                description="stricter",
                min_wallet_health_score=85,
                max_single_tx_sats=1_000_000,
                change_justification="stress regime",
            ),
        )

        out = service.compare_catalog_profiles(
            db=db,
            payload=PolicyCatalogCompareRequest(
                baseline_policy_name="baseline",
                candidate_policy_name="candidate",
            ),
        )

    assert out.changed_thresholds
    assert out.changed_rules
    assert out.risk_level in {"medium", "high"}
