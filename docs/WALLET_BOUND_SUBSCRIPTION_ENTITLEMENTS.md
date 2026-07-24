# Wallet-bound Subscription Entitlements

A Subscription Entitlement is the authoritative commercial and technical access object for Wallet-first Proof-of-Access Auth PQ v2. It defines plan code, API scopes, metric groups, limits, validity, assurance requirements, issuer signature metadata, and lifecycle state.

Payment is not authentication. Invoice creation is not settlement. LNURL-auth is not subscription payment proof. Lightning Address is not identity. A Subscription Entitlement is not a bearer credential and cannot authorize an API request by itself.

Protected access still requires an active wallet or Lightning principal, active device, active PoP session, matching principal binding, permitted scope, permitted metric group, available quota, clean revocation state, and a Policy Engine allow decision.

## Subjects

Supported subject types are `bitcoin_wallet_principal`, `lightning_wallet_principal`, `access_certificate`, `business_workspace`, `business_role`, `payregister_owner`, `payregister_device`, `delegated_pass`, and `child_api_key`. Raw Bitcoin addresses, LNURL linking keys, Lightning Addresses, emails, raw Access Passes, and raw sessions are never entitlement subject identifiers.

## Plans, metrics, and limits

The service reuses the central plan catalog for `lite_pass`, `basic_pass`, `plus_pass`, `pro_pass`, `business_pass`, and `enterprise_pass`. API scopes describe actions; metric groups describe data products; limits describe volume, history, interval, child-key, delegated-pass, and concurrent-session ceilings.

## LNURL payment binding

LNURL-funded issuance requires a verified and settled Payment Proof. Duplicate settlement notifications return the existing compatible entitlement. A payment proof cannot be rebound to another principal or plan. payerData email and comments never authorize entitlement issuance.

## Upgrade and downgrade

Upgrades require a new verified payment proof or issuer grant; Pro/Business/Enterprise upgrades require fresh step-up. Upgrades do not silently broaden child API keys. Downgrades narrow scopes, metric groups, and limits, freeze incompatible child objects, invalidate incompatible offline packs, and preserve audit evidence.

## Signatures and PQ metadata

Entitlements use Ed25519 issuer signatures today and include schema, policy, and crypto epochs. PQ signature suites are metadata-ready only; unsupported ML-DSA or SLH-DSA signatures fail closed and are not faked.
