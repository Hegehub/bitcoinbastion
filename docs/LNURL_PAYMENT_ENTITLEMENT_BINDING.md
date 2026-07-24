# LNURL Payment to Subscription Entitlement Binding

This component converts a cryptographically verified, settled Bastion LNURL Payment Proof into a wallet-bound Subscription Entitlement. Invoice issued does not mean paid. Payment Proof is not identity. Lightning Address is not identity. Payment hash and preimage are not login credentials. Activation reference is not sufficient without wallet proof. Bastion never asks for a Bitcoin seed or private key. Subscription access is granted only after settlement verification, principal binding, issuer signing, and Policy Engine approval.

## Trusted flow

LNURL-pay request → BOLT-11 invoice issued → settlement verified → LNURL Payment Proof created → cryptographic principal resolved → Policy Engine evaluated → Subscription Entitlement issued/renewed/upgraded → audit event recorded → payment proof consumption recorded.

## Binding modes

1. **Authenticated checkout** binds a proof to the same active wallet-first PoP principal that created the payment request.
2. **payerData.auth** binds only after a server-verified LNURL-auth payerData proof is converted to an HMAC principal identifier.
3. **Post-payment activation** creates a pending reservation for anonymous checkout. The random activation reference is short-lived, one-time, hashed in storage, scoped to one proof, and not sufficient without fresh Wallet Proof or LNURL-auth.

## Product mapping and operations

The service uses trusted product mappings for `lite_pass`, `basic_pass`, `plus_pass`, `pro_pass`, `business_pass`, and `enterprise_pass`. Amount alone never defines Enterprise access, and `basic_pass` is the stable Basic tier name. Underpayment is rejected. Overpayment behavior is explicit per product policy. Supported operations are new subscription, renewal, upgrade, extension, Business invoice activation, and PayRegister plan activation.

## Policy Engine and issuer boundaries

Policy runs before active entitlement issuance. A successful payment does not override security policy. High-risk upgrades can require step-up. Entitlements are issued through an issuer adapter shaped around the existing Subscription Entitlement service; Bastion signs access rights, not the payment provider or wallet.

## Audit and revocation

Audit events include only safe hashes and low-cardinality fields for binding start, pending principal, policy denial, step-up, entitlement issuance, renewal, upgrade, duplicate, failure, reservation creation/activation/expiry, and payment proof consumption. Revoking an entitlement does not rewrite payment history; revoking a Payment Proof blocks future binding.

## Idempotency and recovery

A deterministic HMAC idempotency key covers payment proof fingerprint, product, operation type, and principal or pending marker. One single-use subscription proof can be consumed once for entitlement issuance. Duplicate settlement or binding callbacks return the existing binding result and do not extend a subscription twice.

## Privacy boundaries

The binding record and audit payloads do not contain raw BOLT-11 invoices, preimages, k1 values, wallet addresses, payerData, activation references, access passes, session tokens, seeds, private keys, email, username, or global user IDs.

## Limitations

The current repository implementation is in-memory for service wiring and tests. Production persistence should add the narrow `lnurl_entitlement_bindings`, reservation, and payment-proof-consumption tables with unique idempotency and proof-purpose constraints when the migration sequence is ready.
