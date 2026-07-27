from app.services.wallet_auth.recovery.errors import RecoveryStateTransitionError
from app.services.wallet_auth.recovery.models import RecoveryCapsuleStatus as S

ALLOWED_TRANSITIONS: dict[S, frozenset[S]] = {
    S.CREATED: frozenset({S.AWAITING_FACTORS}),
    S.AWAITING_FACTORS: frozenset(
        {
            S.FACTOR_VERIFICATION_IN_PROGRESS,
            S.COOLDOWN,
            S.READY_FOR_COMPLETION,
            S.FAILED,
            S.CANCELLED,
            S.EXPIRED,
            S.LOCKED,
        }
    ),
    S.FACTOR_VERIFICATION_IN_PROGRESS: frozenset(
        {S.AWAITING_FACTORS, S.COOLDOWN, S.READY_FOR_COMPLETION, S.FAILED, S.LOCKED}
    ),
    S.COOLDOWN: frozenset({S.READY_FOR_COMPLETION, S.EXPIRED, S.CANCELLED, S.LOCKED}),
    S.READY_FOR_COMPLETION: frozenset({S.COMPLETED, S.EXPIRED, S.LOCKED, S.REVOKED}),
    S.COMPLETED: frozenset({S.REVOKED}),
    S.LOCKED: frozenset(),
    S.FAILED: frozenset(),
    S.CANCELLED: frozenset(),
    S.EXPIRED: frozenset(),
    S.REVOKED: frozenset(),
}


def transition(current: S | str, target: S | str) -> S:
    current_status, target_status = S(current), S(target)
    if target_status not in ALLOWED_TRANSITIONS[current_status]:
        raise RecoveryStateTransitionError("illegal_recovery_state_transition")
    return target_status
