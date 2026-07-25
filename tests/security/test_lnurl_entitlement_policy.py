from app.domain.access.plans import PlanCode
from app.services.lnurl.policy_hooks import LNURLPolicyHooks


def base(**overrides):
    data = dict(principal_hash="hmac:p", subscription_plan=PlanCode.PRO, session_hash="sha256:s", device_key_fingerprint="sha256:d", payment_request_hash="sha256:req", invoice_hash="sha256:invoice", amount_msat=1000, expected_amount_msat=1000)
    data.update(overrides)
    return data


def test_lnurl_entitlement_requires_verified_settlement_and_matching_amount():
    hooks = LNURLPolicyHooks()
    assert hooks.authorize_entitlement_issuance(**base(invoice_status="issued")).reason_code == "payment_not_settled"
    assert hooks.authorize_entitlement_issuance(**base(payment_status="settled", settlement_verified=False)).reason_code == "settlement_not_verified"
    assert hooks.authorize_entitlement_issuance(**base(payment_status="settled", settlement_verified=True, payment_proof_hash="sha256:proof")).allowed
    assert hooks.authorize_entitlement_issuance(**base(payment_status="settled", settlement_verified=True, payment_proof_hash="sha256:proof", amount_msat=999)).reason_code == "amount_mismatch"
