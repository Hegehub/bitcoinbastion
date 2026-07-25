from dataclasses import fields

from app.services.access.policy_context import AccessPolicyContext, AccessPolicyDecision, AuthenticationAssuranceLevel, PolicyActorType, PolicyAuthMethod
import app.services.access.policy_reasons as reasons


def values(enum):
    return {item.value for item in enum}


def test_stable_policy_actor_method_assurance_values():
    assert {"bitcoin_wallet_principal","lightning_wallet_principal","wallet_device","access_certificate","child_api_key","delegated_pass","business_role","payregister_device","bot","service_account","recovery_actor"} <= values(PolicyActorType)
    assert {"bip322","legacy_bitcoin_message","hardware_wallet","air_gapped_wallet","multi_wallet_quorum","lnurl_auth","access_certificate","device_pop","session_pop","child_api_key","delegated_pass","recovery_capsule","internal_service_identity"} <= values(PolicyAuthMethod)
    assert {"compatibility","standard","high_assurance","sovereign"} == values(AuthenticationAssuranceLevel)


def test_structured_decision_contract_and_reason_codes():
    names = {f.name for f in fields(AccessPolicyDecision)}
    assert {"decision","reason_code","actor_type","actor_hash","auth_methods_used","authentication_assurance","requested_action","requested_scope","requested_metric_group","resource_type","resource_hash","requires_quorum","required_quorum","requires_access_certificate","audit_required","offline_allowed","policy_epoch","policy_hash","evaluated_at","safe_user_message","internal_reason_details"} <= names
    for code in ["lightning_principal_not_treasury_proof","lnurl_k1_reused","payment_not_settled","lightning_address_not_identity","quorum_required"]:
        assert code in {v for k, v in vars(reasons).items() if k.isupper()}


def test_policy_context_has_no_secret_bearing_public_fields():
    field_names = {f.name for f in fields(AccessPolicyContext)}
    forbidden = {"bitcoin_address", "lnurl_linking_key", "k1", "signature", "session_token", "private_key", "seed_phrase"}
    assert not (field_names & forbidden)
