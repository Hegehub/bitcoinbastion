"""Safe PayRegister LNURL errors."""
from __future__ import annotations


class PayRegisterLNURLError(ValueError):
    reason_code = "payregister_lnurl_error"
    public_reason = "Payment endpoint temporarily unavailable"

    def to_lnurl_error(self) -> dict[str, str]:
        return {"status": "ERROR", "reason": self.public_reason}


class PayRegisterLNURLEndpointNotFound(PayRegisterLNURLError):
    reason_code = "endpoint_not_found"


class PayRegisterLNURLEndpointDisabled(PayRegisterLNURLError):
    reason_code = "endpoint_disabled"


class PayRegisterLNURLEndpointRevoked(PayRegisterLNURLError):
    reason_code = "endpoint_revoked"


class PayRegisterLNURLNoActiveCheckout(PayRegisterLNURLError):
    reason_code = "no_active_checkout"


class PayRegisterLNURLContextExpired(PayRegisterLNURLError):
    reason_code = "checkout_expired"


class PayRegisterLNURLContextReplaced(PayRegisterLNURLError):
    reason_code = "checkout_replaced"


class PayRegisterLNURLInvalidAmount(PayRegisterLNURLError):
    reason_code = "invalid_amount"


class PayRegisterLNURLInvoiceConflict(PayRegisterLNURLError):
    reason_code = "invoice_conflict"


class PayRegisterLNURLSettlementError(PayRegisterLNURLError):
    reason_code = "settlement_unavailable"


class PayRegisterLNURLPolicyDenied(PayRegisterLNURLError):
    reason_code = "policy_denied"
