# ADR: Bastion Proof-of-Access Auth

## 2. Status

Accepted for implementation planning.

This ADR defines the target architecture. It does not claim the full Proof-of-Access system is already implemented.

## 3. Decision Date

2026-06-30

## 4. Context

Bitcoin Bastion is migrating to a Bitcoin-native, privacy-preserving, accountless access model. The repository currently contains, or may continue to contain during migration, legacy authentication surfaces such as auth endpoints, auth schemas, SDK bearer auth helpers, frontend auth assumptions, tests, and documentation.

The old model is:

```text
email / username
+
password
+
login/register
+
bearer token or JWT
+
user account identity
```

The target model is:

```text
payment proof
+
SHA-256 / HMAC-SHA256 commitments
+
signed Access Certificate
+
Subscription Entitlement Overlay
+
local device key
+
origin-bound challenge
+
Proof-of-Possession session
+
API scopes
+
Metric Entitlements
+
Policy Engine decision
+
Revocation Registry
+
Audit Chain
+
Recovery Layer
+
crypto-agility / post-quantum readiness
```

Primary architectural principle:

> Bastion Auth is not login. Bastion Auth is proof-controlled access.

The user should not prove “who they are”. The user should prove that they hold a valid, non-revoked, subscription-bounded access right and can cryptographically prove possession of the corresponding local device key.

The existing legacy model is incompatible with Bitcoin Bastion’s long-term principles:

- Bitcoin-first.
- Sovereignty-first.
- Privacy-aware.
- No custody.
- Minimum personal data.
- Auditable access.
- Operator-grade policy control.

Classic login/password introduces:

- password storage risk;
- reset-flow risk;
- email dependency;
- support-controlled recovery risk;
- bearer-token theft risk;
- user identity linkage;
- weak long-term cryptographic posture.

## 5. Problem

Bitcoin Bastion needs a production-grade access layer that:

- does not require email;
- does not require password;
- does not require a classic personal account by default;
- does not store backend private keys;
- does not use Bitcoin wallet seed/private keys for authentication;
- does not make Access Pass a bearer token;
- supports subscription-gated API access;
- supports scoped metric entitlements;
- supports revocation;
- supports auditability;
- supports user-controlled recovery;
- supports future post-quantum migration.

## 6. Decision

Bitcoin Bastion will replace legacy email/password/bearer-token authentication with Bastion Proof-of-Access Auth.

The Access Layer will be based on:

```text
Payment Proof
+
SHA-256 / HMAC-SHA256 Commitments
+
Signed Access Certificate
+
Subscription Entitlement Overlay
+
Local Device Key
+
Origin-Bound Challenge
+
Proof-of-Possession Session
+
API Scopes
+
Metric Entitlements
+
Policy Engine
+
Revocation Registry
+
Audit Chain
+
Recovery Layer
+
Crypto-Agility / PQ-Readiness
```

The Access Layer separates four concerns that legacy auth tends to collapse:

1. **Payment/issuance:** evidence that a pass, renewal, grant, or upgrade may be issued.
2. **Possession:** proof that the current device holds the private key bound to the certificate/session.
3. **Authorization:** policy decision over scopes, metrics, quotas, risk, subscription, object access, and revocation status.
4. **Audit/recovery:** tamper-evident event recording and user-controlled recovery paths.

## 7. Non-Negotiable Rules

* No mandatory email fallback.
* No password fallback.
* No support-only recovery.
* No backend private keys.
* No Bitcoin seed/private key for authentication.
* No bearer Access Pass.
* No global user_id as the default access identity.
* No browser-only approval for critical actions.
* No unlimited API key.
* No unchecked metric access.
* No subscription without signed entitlement.
* No critical action without Human Intent Signature.
* No protected API request without Policy Engine decision.
* No recovery path easier than login.
* No fake post-quantum claims.

## 8. Key Concepts

### 8.1 Payment Proof

Payment Proof is evidence that the user has paid for a plan, voucher, renewal, upgrade, or enterprise grant.

Payment Proof does not authenticate the user by itself. Payment Proof only authorizes issuance or renewal of an Access Certificate or Subscription Entitlement.

Supported future payment methods:

- Lightning invoice.
- BTCPay invoice.
- On-chain Bitcoin payment.
- LNURL-pay.
- Manual grant.
- Voucher.
- Renewal payment.
- Subscription upgrade payment.
- Business invoice.
- Enterprise contract grant.

### 8.2 Bastion Access Pass

The user-facing access object.

It may be represented as:

- `BBP-LITE-...`
- `BBP-BASIC-...`
- `BBP-PLUS-...`
- `BBP-PRO-...`
- `BBP-BUSINESS-...`
- `BBP-ENTERPRISE-...`
- `bastion-pass.bbp`

Important:

Bastion Access Pass is not a password. Bastion Access Pass is not a bearer token. Bastion Access Pass is a signed access right that only works with device key possession, challenge signature, active entitlement, Policy Engine approval, and revocation checks.

### 8.3 Access Certificate

An Access Certificate is a signed document proving that a pass exists and has a defined scope, expiry, crypto epoch, issuer signature, and device public key binding.

The backend stores:

- `pass_lookup_hash`;
- `pass_commitment`;
- `certificate_fingerprint`;
- `device_key_fingerprint`;
- issuer metadata;
- scopes;
- expiry;
- status.

The backend must not store:

- raw pass;
- local private key;
- Bitcoin seed;
- recovery phrase;
- wallet private key.

### 8.4 Subscription Entitlement Overlay

Subscription is not merely a string plan value.

It is a signed overlay that defines:

- plan;
- status;
- `valid_from`;
- `valid_until`;
- metric entitlements;
- API scopes;
- limits;
- quotas;
- websocket streams;
- child API key allowance;
- delegated pass allowance;
- issuer signature.

Reason:

Changing the subscription should not require reissuing the base Access Certificate every time.

### 8.5 Local Device Key

The device key proves possession.

The private key:

- remains local;
- is never sent to backend;
- is not a Bitcoin key;
- is not a seed phrase;
- is not stored by Bastion backend.

Device keys may later be backed by:

- Secure Enclave;
- TPM;
- FIDO2;
- hardware access card;
- mobile vault;
- desktop vault.

### 8.6 Origin-Bound Challenge

An Origin-Bound Challenge is a one-time challenge bound to:

- origin;
- certificate fingerprint;
- requested scopes;
- timestamp;
- server nonce;
- expiry.

The challenge prevents generic replay and phishing across origins.

### 8.7 Proof-of-Possession Session

A Proof-of-Possession Session is a short-lived session created after a valid challenge signature.

Critical requests must be signed using request-level PoP.

Request signing should include:

- method;
- path;
- body hash;
- timestamp;
- nonce;
- session identifier;
- signature.

Required headers:

- `X-Bastion-Session`
- `X-Bastion-Timestamp`
- `X-Bastion-Nonce`
- `X-Bastion-Body-Hash`
- `X-Bastion-Signature`

### 8.8 Policy Engine

Every protected access decision must be explicit.

The Policy Engine checks:

- authentication proof;
- subscription status;
- requested scope;
- metric entitlement;
- quota;
- object access;
- risk level;
- device status;
- session status;
- revocation status;
- offline limits;
- business role;
- enterprise policy.

Allowed decisions:

- `allow`
- `deny`
- `upgrade_required`
- `step_up_required`
- `quota_exceeded`
- `metric_not_allowed`
- `revoked`
- `expired`
- `recovery_required`
- `online_check_required`

### 8.9 Revocation Registry

The Revocation Registry must support revoking:

- pass;
- certificate;
- entitlement;
- device;
- session;
- child API key;
- delegated pass;
- offline validity pack;
- issuer key.

Revocation must be checked by:

- session creation;
- protected endpoint dependencies;
- request verifier;
- child key verification;
- recovery flow;
- offline validity refresh.

### 8.10 Audit Chain

Access events must be tamper-evident.

Audit event hash formula:

```text
event_hash = SHA256(previous_event_hash || canonical_event)
```

Audit payloads must not include:

- raw pass;
- raw session token;
- raw recovery phrase;
- private keys;
- Bitcoin seed;
- wallet private keys.

### 8.11 Recovery Layer

Recovery must be user-controlled, cryptographic, auditable, and support-independent.

Recovery must not be easier than login.

Recovery methods:

- recovery code for lower tiers;
- Bastion Recovery Seed;
- device proof;
- recovery quorum;
- cooldown;
- audit event;
- emergency lockdown;
- business/admin quorum.

Important:

Bastion Recovery Seed is not a Bitcoin wallet seed. Bastion must never ask for the user’s Bitcoin wallet seed or private key.

### 8.12 Bastion Recovery Seed

Bastion Recovery Seed is a non-wallet recovery phrase used only for recovering Bastion Access Layer material.

Tiers:

- Lite / Basic / Plus may use 12-word Bastion Recovery Seed.
- Pro / Business / Enterprise should use 24-word Bastion Recovery Seed or stronger recovery setup.

Rules:

- never store raw phrase;
- store only commitment/hash material;
- never accept Bitcoin seed/private key as recovery input;
- UI must warn users that this is not a Bitcoin wallet seed.

### 8.13 Recovery Quorum

For higher tiers, recovery should require multiple factors.

Suggested profiles:

- Plus optional 2-of-3:
  - Desktop Vault.
  - Mobile Vault.
  - 12-word Bastion Recovery Seed.
- Pro 2-of-3:
  - Desktop Vault.
  - Mobile Vault.
  - 24-word Bastion Recovery Seed.
- Business 2-of-3:
  - Owner Vault.
  - Admin Vault.
  - Business Recovery Seed.
- Enterprise 3-of-5:
  - Owner Key.
  - Admin Key.
  - Hardware Key.
  - 24-word Bastion Recovery Seed.
  - Offline Recovery Kit.

### 8.14 Crypto-Agility and PQ Readiness

The Access Layer must be crypto-agile.

MVP/Production baseline may use classical cryptography first, but object schemas must support:

- `crypto_epoch`;
- `hash_suite`;
- `issuer_signature.alg`;
- `issuer_signature.key_id`;
- optional PQ public key metadata;
- unsupported PQ suite handling.

Do not claim full PQ implementation unless real cryptographic implementation and tests exist.

Future suites:

- ML-KEM for post-quantum session envelope / hybrid key establishment.
- ML-DSA for post-quantum signatures.
- SLH-DSA for backup/root/long-term signatures.
- SHA3-256 and SHAKE256 as secondary/XOF hash suite options.

## 9. Subscription Plans

Canonical plan codes:

- `lite_pass`
- `basic_pass`
- `plus_pass`
- `pro_pass`
- `business_pass`
- `enterprise_pass`

Positioning:

- Lite: observe.
- Basic: use.
- Plus: analyze.
- Pro: automate.
- Business: operate.
- Enterprise: integrate and control.

Commercial plan, API scopes, metric entitlements, and Policy Engine are separate layers:

- **Commercial plan** describes the purchase or contract tier.
- **API scopes** describe allowed API operations.
- **Metric entitlements** describe allowed data families, time intervals, history depth, stream access, and quotas.
- **Policy Engine decisions** decide whether a specific request is allowed at runtime.

A plan alone must never imply unrestricted access. Runtime access depends on signed entitlement state, current session proof, scope, metric, quota, risk, object access, and revocation status.

## 10. Metric Entitlements

Bitcoin Bastion API access is not binary.

Metric groups include:

- `market.basic`
- `bitcoin.network`
- `bitcoin.mempool`
- `market.intelligence`
- `signals.lite`
- `signals.standard`
- `signals.advanced`
- `historical.similarity`
- `trace.lite`
- `trace.standard`
- `trace.advanced`
- `wallet.health`
- `treasury.read`
- `payregister.metrics`
- `enterprise.custom`

Policy Engine must check:

- metric allowed;
- interval allowed;
- history range allowed;
- quota available;
- plan sufficient;
- signature requirement satisfied.

## 11. Target API Surface

### Access API

- `POST /v1/access/payment-intents`
- `GET /v1/access/payment-intents/{payment_intent_id}`
- `POST /v1/access/certificates`
- `POST /v1/access/challenges`
- `POST /v1/access/sessions`
- `GET /v1/access/me`
- `GET /v1/access/me/entitlements`
- `GET /v1/access/me/limits`
- `POST /v1/access/lockdown`

### Recovery API

- `POST /v1/access/recovery/start`
- `POST /v1/access/recovery/verify-seed`
- `POST /v1/access/recovery/verify-share`
- `POST /v1/access/recovery/complete`
- `GET /v1/access/recovery/status`
- `POST /v1/access/recovery/rotate`

### Metrics API

- `GET /v1/metrics/catalog`
- `POST /v1/metrics/query`
- `GET /v1/metrics/usage`

### API Keys

- `POST /v1/access/api-keys`
- `GET /v1/access/api-keys`
- `DELETE /v1/access/api-keys/{key_id}`

### Subscription API

- `POST /v1/access/upgrade-intent`
- `POST /v1/access/subscription-renewal`
- `GET /v1/access/subscription`
- `GET /v1/access/subscription/history`

## 12. Target Repository Structure

Target files and areas:

```text
app/domain/access/
app/schemas/access.py
app/db/models/access.py
app/services/access/
app/services/access/crypto/
app/services/access/payments/
app/services/access/recovery_seed.py
app/services/access/recovery_quorum.py
app/api/v1/access.py
app/api/access_dependencies.py
tests/security/test_no_password_auth.py
tests/security/test_no_bearer_access_pass.py
tests/security/test_no_bitcoin_seed_auth.py
tests/integration/test_access_full_flow.py
sdk/python/bitcoin_bastion_sdk/auth.py
sdk/typescript/src/auth.ts
frontend access routes
frontend access routes if Reflex frontend remains active
```

The future structure should keep domain logic separate from transport logic:

- `app/domain/access/` owns concepts and invariants.
- `app/services/access/crypto/` owns canonicalization, hashing, signature verification, challenge validation, nonce/timestamp validation, and crypto suite handling.
- `app/services/access/payments/` owns payment-provider abstractions and proof normalization.
- `app/services/access/recovery_seed.py` and `app/services/access/recovery_quorum.py` own recovery primitives and policy-independent recovery validation.
- `app/api/access_dependencies.py` owns request-time access context extraction, proof verification, policy invocation, and revocation checks.

## 13. Migration Plan

### Stage 1 — Audit and freeze legacy auth

- identify all legacy auth surfaces;
- do not change runtime behavior yet.

### Stage 2 — Add Access Layer beside legacy auth

- domain;
- schemas;
- models;
- migrations;
- crypto primitives;
- payment provider abstraction.

### Stage 3 — Implement core Proof-of-Access flow

- payment intent;
- certificate issuer;
- subscription entitlement;
- challenge;
- session;
- request verifier;
- revocation;
- audit.

### Stage 4 — Add Access API and dependencies

- access router;
- access dependencies;
- policy engine.

### Stage 5 — Protect premium endpoints

- trace business;
- trace enterprise;
- treasury;
- metrics query;
- policy management;
- webhook management;
- developer API key management;
- dashboard private APIs.

### Stage 6 — Migrate SDKs

- Python SDK;
- TypeScript SDK;
- request signing;
- pass/session redaction.

### Stage 7 — Migrate frontend

- remove login/register UI;
- add access checkout;
- add access import;
- add access status;
- add recovery;
- add lockdown.

### Stage 8 — Disable legacy auth

- `/auth/register` no longer creates password account;
- `/auth/login` no longer issues bearer token;
- return `410 Gone` or explicit `legacy_auth_disabled` response.

### Stage 9 — Remove legacy artifacts

- remove password schemas;
- remove password hashing;
- remove bearer token helpers;
- remove JWT dependency if unused;
- remove old auth tests.

### Stage 10 — Add release gate

- prevent reintroduction of password login;
- prevent bearer Access Pass fallback;
- verify every protected endpoint calls Policy Engine.

## 14. Compatibility Policy

Backward compatibility with legacy password auth is intentionally limited.

Allowed temporary compatibility:

- legacy endpoints may remain only to return explicit deprecation/410 responses;
- SDKs may temporarily expose old auth classes as deprecated stubs;
- docs may mention legacy auth only in migration notes.

Not allowed:

- hidden password login;
- hidden bearer fallback;
- bearer Access Pass mode;
- automatic account creation from email;
- support reset path.

## 15. Threat Model

| Threat | Mitigation |
|---|---|
| 1. Stolen Access Pass file | Pass is not bearer. Requires local device key, challenge, session, policy, revocation check. |
| 2. Phishing | Origin-bound challenge, Vault approval, Trust Phrase, Human Intent Signature. |
| 3. Replay attack | Nonce registry, one-time challenge, timestamp freshness, request digest. |
| 4. Session theft | Short-lived sessions, PoP request signing, revocation. |
| 5. Database leak | No private keys, no raw pass, HMAC lookup hashes, separated identifiers. |
| 6. API key leak | Child keys, scopes, expiry, quotas, revocation. |
| 7. Recovery abuse | No support-only reset, quorum recovery, cooldown, audit. |
| 8. Malicious browser extension | Critical actions outside browser, Vault/mobile/hardware confirmation, signed intent manifest. |
| 9. Offline abuse | Short offline validity, limited scopes, revocation epoch, online refresh. |
| 10. Subscription abuse | Signed entitlements, metric checks, quota enforcement, downgrade freezing. |
| 11. Fake PQ claims | Only expose implemented crypto suites. Unsupported PQ suite must fail safely. |

## 16. Consequences

### Positive

- removes password storage risk;
- reduces personal data collection;
- aligns with Bitcoin-native sovereignty model;
- supports subscription-gated API access;
- supports revocation and auditability;
- improves security over bearer-only auth;
- enables future wallet-bound / device-bound / hardware-backed access.

### Negative

- more complex than normal login;
- recovery UX is harder;
- SDKs must implement request signing;
- frontend flow is less familiar;
- support process must change;
- payment-provider dependency becomes critical;
- policy bugs can block access.

## 17. Alternatives Considered

### 17.1 Keep email/password/JWT

Rejected because it contradicts privacy, sovereignty, and long-term security goals.

### 17.2 Use only API keys

Rejected because API keys become bearer secrets and do not provide rich policy/recovery/session semantics.

### 17.3 Use Lightning payment as login

Rejected because payment proof is not authentication and does not prove continuing possession.

### 17.4 Use Bitcoin wallet seed/private key for auth

Rejected categorically because Bastion must never ask for or handle Bitcoin wallet secrets.

### 17.5 Use OAuth/Social Login

Rejected for default access because it introduces third-party identity dependency.

### 17.6 Use Web3 wallet-style auth

Rejected as default because Bitcoin Bastion should stay Bitcoin-native and avoid EVM-style identity assumptions.

## 18. Implementation Boundaries

This ADR does not implement the system.

This ADR does not create database migrations.

This ADR does not enable BTCPay.

This ADR does not implement PQ cryptography.

This ADR does not remove legacy auth yet.

This ADR defines the target architecture and migration constraints.

## 19. Acceptance Criteria for Future Implementation

The migration is complete only when:

- `/auth/register` no longer creates password accounts;
- `/auth/login` no longer issues bearer/JWT tokens;
- `Authorization: Bearer` is no longer the main protected API mechanism;
- raw Access Pass cannot be used as bearer auth;
- every private endpoint uses Access dependency;
- Policy Engine is called for every protected request;
- payment proof can issue certificate/entitlement;
- challenge/session flow works;
- critical requests can require PoP request signing;
- recovery does not accept Bitcoin seed/private key;
- SDKs support Proof-of-Access headers;
- frontend no longer shows password login;
- logs redact pass/session/recovery material;
- release gates prevent legacy auth reintroduction.

## 20. Validation Notes

Original Prompt 01 ADR creation was documentation-only. Prompt 02 validation for the pure domain layer is recorded in the Prompt 02 pull request and final response.

No runtime authentication behavior was changed.

No migrations were changed.

## 21. Expected Follow-Up

1. ADR path: `docs/ADR_BASTION_PROOF_OF_ACCESS_AUTH.md`.
2. Key decision: Bitcoin Bastion will replace legacy email/password/bearer-token authentication with Bastion Proof-of-Access Auth.
3. Legacy auth replacement target: payment proof, commitments, signed Access Certificate, Subscription Entitlement Overlay, local device key, origin-bound challenge, Proof-of-Possession session, API scopes, Metric Entitlements, Policy Engine, Revocation Registry, Audit Chain, Recovery Layer, and crypto-agility / PQ-readiness.
4. Next recommended prompt: **Prompt 02/33 — Access domain package**.

## 22. Implementation Notes

Prompt 02 introduced the pure domain layer for plan codes, scopes, metric groups, plan limits, and policy decisions.
