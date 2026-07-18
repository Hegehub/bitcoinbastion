# LNURL_PRIVACY.md

## LNURL comment privacy and retention

Raw LNURL comments are not stored by default. Bastion persists `comment_present`, a normalized comment hash, character count, deterministic classification, storage mode, and retention expiry. Raw storage requires explicit merchant/business policy, encryption at rest, short retention, restricted operator access, deletion support, and exclusion from analytics/training datasets by default.

Comments must not be copied into Access Certificates, Subscription Entitlements, Wallet Principals, Lightning Principals, sessions, device bindings, revocation subjects, policy subjects, metrics labels, API keys, recovery capsules, or transparency checkpoints.

## payerData.auth privacy

Bastion stores HMAC or fingerprint commitments for payerData.auth evidence rather than raw payerdata JSON, raw LNURL linking keys, raw k1 challenges, or raw signatures. Lightning Principals use HMAC lookup identifiers and product-specific pseudonyms to reduce cross-product correlation; payerData.email/name/identifier remain disabled unless a later explicit policy enables them.
