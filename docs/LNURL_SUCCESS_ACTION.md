# LNURL successAction activation

LNURL `successAction` is post-payment presentation metadata. It does not prove payment settlement, authenticate a principal, issue a session, or authorize access.

Bastion supports the standard `message` and `url` forms only. Text is limited to 144 Unicode characters, must come from server-controlled templates, and must not contain recovery material, Access Passes, session tokens, invoices, preimages, seeds, private keys, or unrestricted payer data.

## URL activation model

URL actions point only at Bastion-controlled routes such as `/access/activate/{opaque_reference}`, `/access/status/{opaque_reference}`, `/receipts/{opaque_reference}`, `/payregister/receipts/{opaque_reference}`, `/vault/setup/{opaque_reference}`, and `/business/onboarding/{opaque_reference}`. The URL host must match the configured LNURL callback host. Clearnet URLs require HTTPS; onion HTTP remains disabled unless explicit onion mode is configured.

Activation references are at least 32 random bytes encoded for URLs. Bastion stores only an HMAC-SHA256 lookup hash with a server activation pepper. The raw reference is returned only in the `successAction` URL, is single-purpose, expires, and can be revoked or refunded. The activation reference is not a bearer credential and opening it does not create a PoP session or Access Pass.

## State machine

Activation records move through `created`, `invoice_issued`, `payment_pending`, `payment_settled`, `entitlement_pending`, `ready`, `opened`, `completed`, `expired`, `revoked`, `refunded`, and `failed`. `created` and `invoice_issued` do not mean paid. `payment_settled` does not necessarily mean the entitlement exists. `ready` requires verified settlement, an immutable Payment Proof, and an active Subscription Entitlement for subscription purposes.

## Settlement and entitlement checks

The activation service consumes trusted settlement, Payment Proof, entitlement, revocation, and policy state from earlier services. It never trusts frontend redirects, wallet UI state, payer comments, payerData email/name, Lightning Address, payment hash, preimage, or invoice issuance as authorization. Subscription completion requires settlement, Payment Proof, active entitlement, non-revoked state, unexpired reference, and Policy Engine approval.

## PayRegister receipts

PayRegister receipt links use opaque activation references under `/payregister/receipts/{opaque_reference}`. Public receipt status may include safe receipt references and settlement state, but must not expose cashier principals, merchant API keys, customer wallet identifiers, LNURL linking keys, or refund controls.

## Revocation, refunds, and privacy

Refunded payments move activation to `refunded`; revoked entitlements or compromised activation references move activation to `revoked`. Historical audit events remain immutable. Audit and metric payloads use hashes, purpose, low-cardinality status, and reason codes only; they must not include raw activation references, invoices, preimages, sessions, Access Passes, wallet addresses, linking keys, recovery phrases, or private keys.

Wallet support for successAction varies. Bastion must provide safe recovery through authenticated payment history or receipt lookup when a wallet does not display successAction, without weakening settlement or principal proof requirements.
