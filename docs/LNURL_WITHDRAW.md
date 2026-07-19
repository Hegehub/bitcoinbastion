
## LNURL-withdraw callback verifier

Wallet callbacks use `GET /v1/lnurl/withdraw/callback/{withdraw_id}?k1=...&pr=...` and return LNURL-compatible JSON: `{"status":"OK"}` on acceptance or `{"status":"ERROR","reason":"..."}` for protocol-level failures. A valid callback only proves that the request reference, single-use `k1`, and BOLT-11 invoice match an issued withdraw request; it does not authorize or execute a Lightning payment.

The verifier rejects malformed, expired, reused, or mismatched `k1` values; wrong-network invoices; amountless invoices by default; invoices outside the authorized min/max bounds; expired invoices; invoices with insufficient remaining TTL; duplicate invoice hashes; and duplicate payment-hash commitments. Accepted callbacks store the invoice through a protected invoice-store boundary, attach only invoice/payment-hash commitments to the withdraw record, move the request to `invoice_received`, and emit an `lnurl_withdraw_policy_handoff_created` audit event for later Policy Engine evaluation.

A valid LNURL-withdraw callback is not sufficient authorization to transfer funds. Bastion must complete Policy Engine evaluation before a payout is queued. The callback verifier never calls a Lightning node, never marks a withdraw request paid, never creates a session, and never treats the receipt of a BOLT-11 invoice as settlement or entitlement evidence.
