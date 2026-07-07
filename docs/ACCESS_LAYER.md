# Bastion Proof-of-Access Auth

Bastion Proof-of-Access Auth is the Bitcoin Bastion authorization model for protected APIs. It replaces legacy email/password registration, password login, JWT bearer sessions, and generic API-key access with payment proof, issuer-signed access rights, subscription entitlements, device possession, request signatures, revocation checks, policy decisions, and tamper-evident audit events.

## Why password auth was removed

Password login creates account databases, reset channels, bearer sessions, and support workflows that are poor matches for a no-custody Bitcoin-native system. Bastion protected access is now based on:

1. Create an Access payment intent.
2. Pay the invoice through the configured provider.
3. Verify payment proof.
4. Issue an Access Certificate.
5. Issue a Subscription Entitlement.
6. Create an origin-bound challenge.
7. Sign the challenge with a Bastion device key.
8. Create a short-lived Proof-of-Possession session.
9. Sign protected requests.
10. Let the Policy Engine decide access.

No mandatory email address is required for protected API authentication, and `/api/v1/auth/register` and `/api/v1/auth/login` remain disabled compatibility stubs only.

## Access Pass is not a bearer token

A Bastion Access Pass is setup material used to bind a certificate/session flow. It must not be sent on every request and must never be documented as a generic authorization-header credential. Access Pass alone does not unlock protected access. Protected calls require an active PoP session, signed request headers when required, active entitlement, non-revoked artifacts, and a Policy Engine allow decision.

## Bitcoin seed and private-key boundary

Bastion will never ask for your Bitcoin seed. Bastion will never ask for a Bitcoin private key. Bastion Recovery Seed is not a Bitcoin wallet seed. Do not enter a Bitcoin wallet seed, xprv, WIF key, wallet file, or hardware-wallet secret into Bastion. Backend services do not store user private keys, do not derive Bitcoin wallet keys, and do not sign Bitcoin transactions.

## Plan model

The stable plan codes are:

- `lite_pass`
- `basic_pass`
- `plus_pass`
- `pro_pass`
- `business_pass`
- `enterprise_pass`

Plan code naming is part of the public contract. Lower-tier plans must receive structured denial or upgrade responses rather than premium data leakage.

## Scope and metric entitlement model

Scopes describe API capabilities such as market read, trace read, policy management, treasury review, child-key management, delegated-pass creation, and business/enterprise operations. Metric entitlements describe allowed metric groups, quotas, limits, and offline-validity behavior. Child keys and delegated passes must be narrower than parent certificates, parent scopes, parent metric entitlements, and current subscription plan.

## Revocation model

The Revocation Registry limits damage from lost sessions, child keys, delegated passes, certificates, devices, entitlements, issuer keys, and lockdown events. A revoked or frozen parent must invalidate or freeze dependent sessions, child keys, delegated passes, and offline packs where supported.

## Audit model

The Access Audit Chain records payment, certificate, entitlement, session, recovery, human-intent, child-key, delegation, revocation, and lockdown events. Audit payloads contain hashes/fingerprints and policy decisions, not raw passes, raw sessions, raw recovery phrases, signatures, private keys, or Bitcoin seed material.

## Lockdown model

Emergency Lockdown freezes active sessions, revokes or freezes child API keys, revokes delegated passes, and leaves the recovery path available. Lockdown is policy-bounded, audited, and not reversible through an ordinary browser-only session.

## Recovery model

Recovery is user-controlled and support-independent. Lite, Basic, and Plus use 12-word Bastion Recovery Seed profiles; Pro, Business, and Enterprise use stronger 24-word or quorum-based profiles. Support cannot unilaterally recover high-tier access.

## Limitations

- Browser UI is an interface, not the root of trust; production signing should use Vault/device custody.
- Post-quantum variable names are reserved for crypto agility unless real ML-KEM, ML-DSA, or SLH-DSA implementations are integrated and tested.
- BTCPay may be disabled by default and must be configured before production invoice use.
- Manual grants must remain disabled in production unless a documented internal approval process exists.
- Offline validity packs and some enterprise policy hooks may be planned or partial; do not treat them as live unless OpenAPI exposes them and tests cover them.
