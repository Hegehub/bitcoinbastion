# LNURL Withdraw Risk Controls

LNURL-withdraw is a payout transport, not an authorization system. A valid `k1` is never sufficient to receive funds; payout authorization requires an active request, policy approval, limit checks, invoice validation, idempotency, and audit evidence.

## Purpose and state model

The risk layer defines stable purpose, risk, decision, failure, and state enums for subscription refunds, PayRegister refunds, rewards, partner payouts, bug bounties, faucets, and administrative adjustments. Payment execution is split into `payment_queued`, `payment_in_flight`, `payment_succeeded`, and `settlement_confirmed`; a single paid boolean is intentionally avoided.

## Limit hierarchy

Effective payout limits are the minimum of global, purpose, principal, business, merchant, role, device, incident, and original-payment refundable balance ceilings. Mainnet withdraw and administrative adjustments are disabled by default, and faucet purposes are rejected on Bitcoin mainnet.

## Refund accounting

Refundable balance is calculated as original settled amount minus confirmed refunds minus active reservations. Terminal failures release reservations; provider timeouts and ambiguous in-flight states retain reservations until reconciliation resolves the outcome.

## Velocity, cooldown, and step-up

Velocity counters track request count, amount, failures, and duplicate destination invoices using hashed identifiers. Cooldowns are server-time based and can be applied after recovery, role changes, repeated failures, or large requests. Higher-value payouts require fresh LNURL-auth and human-intent controls before execution.

## Invoice validation and idempotency

Destination invoices are decoded through the project BOLT-11 abstraction, checked for network, exact amount, expiry, duplicate invoice/payment hash, and sufficient remaining TTL. Execution idempotency binds withdraw request, payment hash, approved amount, and policy hash so retries cannot double-pay.

## Audit, metrics, and operations

Audit payloads and metrics use hashes and low-cardinality labels only; raw k1 values, BOLT-11 invoices, preimages, signatures, session tokens, private keys, seeds, macaroons, and provider credentials are forbidden. Reconciliation compares local state with provider state and never blindly retries ambiguous payments.
