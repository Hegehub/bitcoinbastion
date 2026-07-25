from app.services.lnurl.policy_hooks import LNURLPolicyHooks


def test_policy_engine_unavailable_denies_critical_lnurl_operations():
    def unavailable():
        raise RuntimeError("no policy")
    hooks = LNURLPolicyHooks(policy_engine_factory=unavailable)
    decision = hooks.authorize_withdraw_payment(principal_hash="hmac:p", amount_msat=1000, maximum_allowed_msat=1000)
    assert not decision.allowed
    assert decision.reason_code == "policy_engine_unavailable"


def test_unknown_actor_or_action_denies():
    hooks = LNURLPolicyHooks()
    assert hooks.authorize_auth_login(actor_type="classic_user", principal_hash="hmac:p", k1_status="used", signature_verified=True, domain_matches=True, challenge_action="lnurl_auth_login").reason_code == "unknown_actor_type"
    assert hooks.authorize_auth_login(principal_hash="hmac:p", k1_status="used", signature_verified=True, domain_matches=True, challenge_action="unknown").reason_code == "lnurl_action_mismatch"
