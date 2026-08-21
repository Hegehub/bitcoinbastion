from app.services.bastion_trace.privacy_policy import (
    TracePrivacyAction,
    TracePrivacyPolicy,
)


def test_trace_privacy_policy_is_default_deny_for_unknown_and_secret_fields() -> None:
    policy = TracePrivacyPolicy()
    assert policy.DEFAULT_ACTION is TracePrivacyAction.DENY
    assert policy.decision("claim", "value") is TracePrivacyAction.ALLOW
    assert policy.decision("claim", "internal_rpc_url") is TracePrivacyAction.DENY
    safe = policy.allowlisted(
        "claim",
        {
            "id": "claim:public",
            "value": "bitcoin-mainnet",
            "new_internal_field": "TRACE_PRIVACY_CANARY_NEVER_BROWSER",
        },
    )
    assert safe == {"id": "claim:public", "value": "bitcoin-mainnet"}
    assert "TRACE_PRIVACY_CANARY_NEVER_BROWSER" not in str(safe)
