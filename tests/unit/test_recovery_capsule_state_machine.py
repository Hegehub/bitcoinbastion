import pytest

from app.services.wallet_auth.recovery.errors import RecoveryStateTransitionError
from app.services.wallet_auth.recovery.models import RecoveryCapsuleStatus as S
from app.services.wallet_auth.recovery.state_machine import ALLOWED_TRANSITIONS, transition


def test_every_declared_transition_is_allowed_and_every_other_is_rejected() -> None:
    for current in S:
        for target in S:
            if target in ALLOWED_TRANSITIONS[current]:
                assert transition(current, target) is target
            else:
                with pytest.raises(RecoveryStateTransitionError):
                    transition(current, target)
