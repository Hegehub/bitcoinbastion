from app.domain.access.plans import PlanCode
from app.services.access.policy_context import (
    AccessPolicyContext,
    PolicyActorType,
    PolicyAuthMethod,
)
from app.services.access.policy_engine import AccessPolicyEngine


def _context(**changes: object) -> AccessPolicyContext:
    values = dict(
        actor_type=PolicyActorType.LIGHTNING_WALLET_PRINCIPAL,
        actor_hash="hmac:actor",
        principal_hash="hmac:principal",
        auth_methods=frozenset({PolicyAuthMethod.LNURL_AUTH, PolicyAuthMethod.SESSION_POP}),
        plan_code=PlanCode.PRO,
        effective_scopes={"market:intelligence:read"},
        requested_scope="market:intelligence:read",
        requested_action="read_metric",
        session_id_hash="hmac:session",
        device_id="sha256:device",
    )
    values.update(changes)
    return AccessPolicyContext(**values)


def test_direct_and_inherited_revocation_deny() -> None:
    decision = AccessPolicyEngine().evaluate(
        _context(
            revocation_resolution={
                "revoked": True,
                "inherited_from_parent": True,
                "propagation_status": "complete",
                "scope": "actor_full_tree",
            }
        )
    )
    assert decision.decision == "revoked" and not decision.allowed


def test_stale_offline_epoch_requires_online_check() -> None:
    decision = AccessPolicyEngine().evaluate(_context(offline_epoch_status="stale"))
    assert decision.decision == "online_check_required"


def test_pending_propagation_denies_critical_and_revoked_withdraw_denies() -> None:
    critical = AccessPolicyEngine().evaluate(
        _context(
            requested_action="high-value_lnurl_withdraw",
            is_critical_action=True,
            propagation_status="pending_propagation",
        )
    )
    withdraw = AccessPolicyEngine().evaluate(
        _context(requested_action="lnurl_withdraw_pay", withdraw_revocation_status="revoked")
    )
    assert critical.decision == "revoked"
    assert withdraw.decision == "revoked"
