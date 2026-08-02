from tests.unit.test_wallet_lnurl_access_dependencies import context

from app.api import access_dependencies as deps


def test_wallet_lnurl_artifacts_are_policy_inputs_not_authorization() -> None:
    class Deny:
        def evaluate(self, _context: object) -> object:
            return type("Decision", (), {"allowed": False, "decision": "deny", "reason_code": "mandatory_policy", "human_reason": "Denied."})()

    old = deps.POLICY_ENGINE_FACTORY
    deps.POLICY_ENGINE_FACTORY = Deny
    try:
        for metadata in ({"wallet_proof_verified": True}, {"lnurl_auth_verified": True}, {"subscription_verified": True}):
            try:
                deps.require_policy_decision(context(metadata=metadata), action="protected_read")
            except Exception:
                continue
            raise AssertionError("artifact bypassed mandatory policy")
    finally:
        deps.POLICY_ENGINE_FACTORY = old
