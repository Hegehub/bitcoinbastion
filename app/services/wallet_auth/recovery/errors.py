class RecoveryCapsuleError(ValueError):
    """Secret-free Recovery Capsule failure."""


class RecoveryStateTransitionError(RecoveryCapsuleError):
    pass


class RecoveryFactorError(RecoveryCapsuleError):
    pass


class RecoveryCooldownError(RecoveryCapsuleError):
    pass


class RecoveryPolicyError(RecoveryCapsuleError):
    pass
