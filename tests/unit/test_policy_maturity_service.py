from app.services.citadel.policy_maturity_service import CitadelPolicyService


def test_policy_maturity_exposes_evidence_chain() -> None:
    out = CitadelPolicyService().evaluate(owner_id=9, wallet_health_score=0.8, has_recent_health_report=True)
    chain = out["explainability"]["evidence_chain"]
    assert chain and chain[0]["domain"] == "policy"
