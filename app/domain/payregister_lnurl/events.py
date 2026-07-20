"""PayRegister LNURL audit event names."""
PAYREGISTER_AUDIT_EVENTS = frozenset(
    {
        "payregister_shift_open_requested",
        "payregister_shift_opened",
        "payregister_shift_open_denied",
        "payregister_shift_suspended",
        "payregister_shift_resumed",
        "payregister_shift_close_requested",
        "payregister_shift_closed",
        "payregister_payment_context_created",
        "payregister_payment_context_denied",
        "payregister_lnurl_payment_requested",
        "payregister_lnurl_invoice_issued",
        "payregister_lnurl_payment_settled",
        "payregister_receipt_issued",
        "payregister_receipt_voided",
        "payregister_context_integrity_failed",
        "payregister_terminal_mismatch_detected",
        "payregister_shift_mismatch_detected",
    }
)
