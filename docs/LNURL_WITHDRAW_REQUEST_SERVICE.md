# LNURL-withdraw Request Service

LNURL-withdraw is a payout transport mechanism. It is not authentication, proof of identity, proof of payment ownership, or permission to receive arbitrary funds. A valid `k1` is single-use challenge material and is never sufficient by itself for a valuable payout.

This prompt implements request creation only. It does not parse wallet callbacks, verify submitted BOLT-11 invoices, execute Lightning payments, process refunds, or run payout workers.

## Request lifecycle

The request creation service enforces the prompt 44 state machine through `created`, `policy_pending`, `policy_approved`, `lnurl_issued`, and terminal `expired`, `revoked`, or `cancelled` states. Callback-side states such as `invoice_received`, `payment_pending`, and `paid` are reserved for later prompts.

## Preconditions

Production-value withdraw requests require an authenticated Wallet or Lightning Principal, active device binding, active PoP Session, active principal/device/session status, safe source binding, and a structured Policy Engine `allow` decision. Step-up or deny decisions do not issue LNURLs.

## k1 and callback safety

The service uses the existing LNURL k1 registry to generate 32 random bytes encoded as 64 lowercase hex characters. Raw k1 is embedded only in the initial LNURL payload, never persisted in the withdraw request record or audit payload. Callback URLs are generated from trusted configuration and contain opaque `wdr_...` references, not database IDs, session tokens, principal hashes, or payment provider secrets.

## Amount, expiry, and idempotency

Fixed refunds default to `minWithdrawable == maxWithdrawable == approved_amount_msat`. Amounts are integer millisatoshis and cannot exceed the global maximum, purpose-specific maximum, policy-approved amount, or source binding. Request TTL defaults to 300 seconds and is capped by configuration. Idempotency keys are HMAC-hashed and bind to purpose, principal, source, amount, network, and bounds.

## Audit and revocation

Creation, issuance, expiry, revocation, cancellation, policy denial, and step-up-required conditions are auditable with safe hashes only. Revocation and expiry propagate to the k1 registry so later callback verification can fail closed.

## Limitations

Prompt 45 owns callback verification and atomic k1 consumption. Prompts 46-48 own refund/payout policy integration, PayRegister refund flows, payment execution, risk limits, and payout audit expansion.
