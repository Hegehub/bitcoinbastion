"""Domain errors for PayRegister LNURL cashier/shift context."""
class PayRegisterContextError(ValueError):
    reason_code = "payregister_context_error"


class PayRegisterPolicyDeniedError(PayRegisterContextError):
    reason_code = "policy_denied"


class PayRegisterRevokedError(PayRegisterContextError):
    reason_code = "revocation_enforced"


class PayRegisterShiftInactiveError(PayRegisterContextError):
    reason_code = "shift_inactive"


class PayRegisterTerminalInactiveError(PayRegisterContextError):
    reason_code = "terminal_inactive"


class PayRegisterIntegrityError(PayRegisterContextError):
    reason_code = "context_integrity_failed"
