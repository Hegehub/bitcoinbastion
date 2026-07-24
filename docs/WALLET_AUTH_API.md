# Wallet Auth API Notes

## LNURL-auth Audit Events

The public LNURL-auth API router is implemented separately, but service-layer LNURL-auth transitions already have a wallet-compatible audit contract. Challenge creation, callback verification, Lightning Principal resolution, device binding, session creation, and step-up decisions emit events through the existing Bastion Access Audit Chain rather than a separate LNURL audit ledger.

Operator-facing audit responses should expose only hashes, fingerprints, event type, outcome, policy reference, timestamps, and reason codes. They must not expose raw `k1`, raw LNURL linking keys, wallet signatures, raw session tokens, Access Passes, private keys, seeds, mnemonics, recovery material, or payment preimages.

Callback and replay failures use generic public protocol responses, while the audit event stores safe internal reason codes such as `signature_invalid`, `k1_reused`, `domain_mismatch`, or `policy_denied`.

## LNURL activation links

LNURL activation references are opaque, short-lived, HMAC-hashed-at-rest lookup values. They are not passwords, payment proofs, Access Passes, PoP sessions, preimages, or recovery factors. Completion of subscription activation through the API must require the expected purpose, server-side settlement/proof/entitlement state, and fresh wallet/device/session context when policy requires it. Bastion never asks for a Bitcoin seed or private key in an activation request.


## Wallet-bound Subscription Entitlements

Wallet-bound Subscription Entitlements define plan, scopes, metric groups, quotas, validity, assurance, and issuer signature metadata for Bitcoin and Lightning principals. They are not bearer credentials: protected API access still requires an active principal, active device, PoP session, matching entitlement binding, revocation checks, and Policy Engine allow decision. See `docs/WALLET_BOUND_SUBSCRIPTION_ENTITLEMENTS.md`.
