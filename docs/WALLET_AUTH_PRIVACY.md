# Wallet Auth Privacy Notes

## LNURL-auth Audit Data Minimization

LNURL-auth audit records are designed for tamper-evident security accountability without creating a global wallet identity. The adapter records only privacy-preserving identifiers: `principal_hash`, `lnurl_key_hash`, `challenge_hash` or `k1_hash`, `session_hash`, auth-domain hashes, device fingerprints, policy hashes, and reason codes.

Raw LNURL linking keys, `k1` values, signatures, wallet addresses, raw session tokens, Access Passes, payer data, recovery material, private keys, wallet seeds, mnemonics, xprv material, and payment preimages are prohibited in audit payloads. Audit events preserve chain integrity through canonical payload hashing and `previous_event_hash`/`event_hash` links; retention minimization should preserve those chain fields even when payload detail is later reduced.

LNURL-auth remains domain-specific. Audit correlation must not imply legal identity, on-chain Bitcoin ownership, paid entitlement, or authorization for critical actions without separate Device Binding, PoP Session, Subscription Entitlement, Policy Engine, Revocation Registry, and step-up evidence.
