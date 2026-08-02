from app.api import access_dependencies as deps
from app.domain.access.context import AccessAuthMethod, AccessPrincipalType
from tests.unit.test_wallet_lnurl_access_dependencies import context


def test_bitcoin_and_lnurl_contexts_reach_same_policy_engine() -> None:
    seen: list[str] = []

    class Allow:
        def evaluate(self, policy_context: object) -> object:
            seen.append(str(getattr(policy_context, "principal_type")))
            return type("Decision", (), {"allowed": True})()

    old = deps.POLICY_ENGINE_FACTORY
    deps.POLICY_ENGINE_FACTORY = Allow
    try:
        deps.require_policy_decision(context(), action="protected_read")
        deps.require_policy_decision(
            context(principal_type=AccessPrincipalType.LIGHTNING_WALLET_PRINCIPAL, auth_method=AccessAuthMethod.LNURL_AUTH),
            action="protected_read",
        )
    finally:
        deps.POLICY_ENGINE_FACTORY = old
    assert len(seen) == 2
