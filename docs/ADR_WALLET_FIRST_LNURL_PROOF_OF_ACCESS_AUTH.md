# ADR: Wallet-first + LNURL Proof-of-Access Auth PQ v2

## 1. Status

Accepted for implementation planning.

This ADR is architecture and implementation-planning documentation only. It does not claim production completion and does not introduce runtime behavior, database models, migrations, API routes, SDK behavior, frontend behavior, wallet custody, BIP-322 verification, LNURL verification, Lightning node integration, or post-quantum signature implementation.

This ADR extends `docs/ADR_BASTION_PROOF_OF_ACCESS_AUTH.md`. The earlier ADR remains the baseline for the completed Proof-of-Access Auth layer; this ADR governs the Wallet-first + LNURL v2 evolution and supersedes any earlier planning assumption that Payment Proof / Access Certificate is the primary actor for new wallet-first flows.

## 2. Context

Bitcoin Bastion has moved away from classic authentication patterns:

- no mandatory email;
- no password login;
- no username/password account;
- no Google OAuth as primary identity;
- no classic register/login account flow;
- no bearer Access Pass;
- no backend private keys;
- no Bitcoin seed/private key for authentication;
- no support-only recovery.

The previous Bastion Proof-of-Access Auth layer introduced:

- Payment Proof;
- Access Certificate;
- Subscription Entitlement;
- Device Key;
- Proof-of-Possession Session;
- Policy Engine;
- Revocation Registry;
- Audit Chain;
- Recovery;
- PQ-ready crypto-agility for Bastion-issued objects.

The v2 architecture changes the primary actor:

- **Before:** Payment Proof / Access Certificate first.
- **After:** Wallet Proof / Wallet Principal first.

Wallet-first is not wallet-only. Wallet proof becomes the primary registration and authentication mechanism, but wallet proof alone is not full authorization.

LNURL adds a Lightning-native adapter layer for:

- LNURL-auth;
- LNURL-pay;
- Lightning Address;
- LNURL-withdraw;
- LNURL-verify;
- `successAction`;
- `commentAllowed`;
- `payerData.auth`.

LNURL-native is not LNURL-only. LNURL-auth proves Lightning wallet control for a domain-specific linking key, but it does not prove on-chain Bitcoin ownership, legal identity, treasury ownership, subscription entitlement, request possession, or final authorization.

## 3. Decision

Bitcoin Bastion will adopt **Wallet-first Proof-of-Access Auth PQ v2**.

Target formula:

```text
Wallet Proof
+ Wallet Principal
+ Lightning Principal
+ Device Key
+ Proof-of-Possession Session
+ Subscription Entitlement
+ Policy Engine
+ Audit Chain
+ Revocation Registry
+ optional Access Certificate
+ optional Bastion LNURL Layer
+ optional PQ issuer chain
= Bastion Wallet-first Proof-of-Access Auth PQ v2
```

Core security law:

- Wallet-first is not wallet-only.
- LNURL-native is not LNURL-only.
- Wallet proves control.
- LNURL-auth proves Lightning wallet control.
- Device proves continuity.
- PoP Session proves request possession.
- Subscription Entitlement defines allowed API surface.
- Policy Engine proves permission.
- Audit Chain proves history.
- Revocation Registry limits damage.
- Access Certificate remains optional high-assurance hardening layer.

Primary registration/authentication adapters:

### A. Bitcoin Wallet Proof Adapter

- BIP-322 is the preferred Bitcoin ownership/control proof.
- Legacy Bitcoin message signature is a limited compatibility fallback only.
- Hardware wallet, air-gapped, and quorum proofs support high-assurance modes.

### B. Lightning Proof Adapter

- LNURL-auth is a Lightning-native login, registration, linking, and step-up adapter.
- LNURL-auth creates or verifies a Lightning Principal.
- LNURL-auth does not by itself grant full protected API access.

### C. Lightning Payment Adapter

- LNURL-pay supports subscription checkout, PayRegister payments, static QR/NFC payment links, and merchant flows.
- Lightning Address supports human-readable LNURL-pay discovery.
- LNURL-verify or internal node/provider verification confirms payment settlement.
- `successAction` supports post-payment activation/receipt UX.
- `commentAllowed` is untrusted metadata only.
- `payerData.auth` is optional payment-auth binding.

### D. Withdraw Adapter

- LNURL-withdraw supports controlled refunds, cashback, rewards, bug bounty payouts, partner payouts, PayRegister refunds, and testnet/signet faucets.
- LNURL-withdraw must be policy-gated before QR issuance for valuable payouts.

## 4. Final architecture

```text
Bastion Proof-of-Access Auth PQ v2
├── Bitcoin Wallet Proof Adapter
│   ├── BIP-322
│   ├── legacy message signing fallback
│   ├── hardware wallet proof
│   └── air-gapped / quorum proof
│
├── Bastion LNURL Layer
│   ├── LNURL-auth
│   ├── LNURL-pay
│   ├── Lightning Address
│   ├── LNURL-withdraw
│   ├── LNURL-verify
│   ├── successAction
│   ├── commentAllowed
│   └── payerData.auth
│
├── Principal Layer
│   ├── BitcoinWalletPrincipal
│   └── LightningWalletPrincipal
│
├── Device Binding Layer
├── PoP Session Layer
├── Subscription Entitlement Layer
├── Metric Entitlement Layer
├── Policy Engine
├── Revocation Registry
├── Audit Chain
├── Recovery Capsule
├── Optional Access Certificate
├── Optional Offline Validity Pack
└── PQ-ready Issuer Chain
```

## 5. Primary concepts

### 5.1 Wallet Proof

Wallet Proof is proof of control over a Bitcoin or Lightning wallet key.

It can be:

- BIP-322 proof;
- legacy Bitcoin message signature fallback;
- hardware wallet proof;
- LNURL-auth proof;
- air-gapped proof;
- multi-wallet quorum proof.

Wallet Proof does not equal full authorization.

### 5.2 Wallet Principal

Wallet Principal is the cryptographic actor created after verified wallet proof.

It is not:

- personal identity;
- `user_id`;
- email account;
- KYC profile;
- Bitcoin address as public account id.

Wallet Principal must use privacy-preserving identifiers:

- `principal_hash`;
- `address_hash`;
- `script_pubkey_hash`;
- `lnurl_key_hash`;
- per-product pseudonym.

### 5.3 Lightning Principal

Lightning Principal is a principal created or verified through LNURL-auth.

It is based on domain-specific Lightning wallet linking key material.

It must not be treated as:

- legal identity;
- global identity;
- proof of treasury ownership;
- on-chain Bitcoin ownership proof.

### 5.4 Device Key

Device Key provides continuity and request possession.

Reasons:

- Wallets should not sign every API request.
- Cold wallets must not be used for routine login.
- Routine API access must use PoP sessions.
- Devices need risk scoring and revocation.

### 5.5 PoP Session

After wallet proof or LNURL-auth, Bastion issues a short-lived Proof-of-Possession session.

Protected API requests must use:

- session;
- timestamp;
- nonce;
- body hash;
- request signature;
- Policy Engine decision.

Wallet proof alone must not access protected APIs.

### 5.6 Subscription Entitlement

Subscription Entitlement defines commercial and technical API access.

It must bind to:

- Wallet Principal; or
- Lightning Principal; or
- optional Access Certificate, depending on flow.

It must define:

- plan;
- metric groups;
- scopes;
- quotas;
- limits;
- expiry;
- issuer signature;
- `crypto_epoch`.

### 5.7 Access Certificate

Access Certificate remains an optional high-assurance hardening layer.

It is required or recommended for:

- Pro automation;
- Business roles;
- Enterprise;
- Sovereign mode;
- PayRegister local mode;
- offline validity packs;
- delegated passes;
- recovery quorum;
- PQ issuer chain;
- hardware-backed vaults.

Access Certificate must not become bearer access.

## 6. Bastion LNURL Layer

The Bastion LNURL Layer is a Lightning-native adapter layer.

Preferred package layout:

```text
app/domain/lnurl/
app/services/lnurl/
app/api/v1/lnurl.py
```

This location is preferred over nesting entirely under `app/services/access/lnurl/` because LNURL includes auth, pay, withdraw, verify, Lightning Address, payerData, successAction, and PayRegister flows. It is broader than access-only authentication.

LNURL layer responsibilities:

- LNURL-auth challenge generation;
- LNURL-auth callback verification;
- k1 registry and replay protection;
- Lightning Principal creation;
- LNURL-auth step-up;
- LNURL-pay subscription request creation;
- LNURL-pay callback invoice creation;
- LNURL-verify settlement confirmation;
- Payment Proof creation;
- Subscription Entitlement binding;
- Lightning Address discovery endpoints;
- LNURL-withdraw request and callback handling;
- `successAction` activation/receipt UX;
- `commentAllowed` handling as untrusted metadata;
- `payerData.auth` handling;
- PayRegister static QR / NFC payment flows;
- LNURL-specific audit events;
- LNURL-specific revocation targets;
- LNURL wallet compatibility policy.

## 7. LNURL-auth decision

LNURL-auth will be supported as Lightning-native registration, login, link, and step-up flow.

Required actions:

- `register`;
- `login`;
- `link`;
- `auth`.

Bastion internal mapping:

- `register` → `wallet_principal_create`;
- `login` → `wallet_principal_authenticate`;
- `link` → `bind_lightning_principal`;
- `auth` → `step_up_for_sensitive_action`.

Security requirements:

- `k1` must be 32 random bytes.
- `k1` must be single-use.
- `k1` must expire quickly.
- `k1` must be bound to domain.
- `k1` must be bound to action.
- `k1` must be bound to policy intent.
- Unexpected `k1` must be rejected.
- Used `k1` must be removed or marked used.
- Callback must verify key and DER-encoded ECDSA signature.
- LNURL-auth must create or verify Lightning Principal.
- LNURL-auth must not grant full access without Device Key, PoP Session, and Policy Engine.

## 8. LNURL-pay decision

LNURL-pay will be supported for:

- Lite / Basic / Plus / Pro subscriptions;
- Business invoice flows;
- Enterprise contract payment flows where applicable;
- PayRegister payments;
- static QR checkout;
- NFC payment links;
- merchant terminal flows.

Rules:

- Invoice generated does not mean invoice settled.
- Subscription entitlement must not be issued until payment is verified as settled.
- Payment metadata must be canonicalized and auditable.
- User comments are untrusted metadata.
- Payment proof must store hashes/fingerprints, not sensitive raw payment data.
- Optional `payerData.auth` can bind payment and Lightning Principal.

## 9. Lightning Address decision

Lightning Address support will be added for product and merchant payment routing.

Examples:

- [lite@bitcoin-bastion.com](mailto:lite@bitcoin-bastion.com)
- [basic@bitcoin-bastion.com](mailto:basic@bitcoin-bastion.com)
- [plus@bitcoin-bastion.com](mailto:plus@bitcoin-bastion.com)
- [pro@bitcoin-bastion.com](mailto:pro@bitcoin-bastion.com)
- [business@bitcoin-bastion.com](mailto:business@bitcoin-bastion.com)
- [store-123@payregister.bitcoin-bastion.com](mailto:store-123@payregister.bitcoin-bastion.com)
- [cashier-01@merchant-domain.com](mailto:cashier-01@merchant-domain.com)

Rules:

- Lightning Address is payment UX, not identity by itself.
- Lightning Address must not become `user_id`.
- Lightning Address endpoints must return LNURL-pay-compatible responses.
- Custom merchant domains must have domain policy and audit trail.

## 10. LNURL-withdraw decision

LNURL-withdraw will be supported only for controlled payouts.

Use cases:

- subscription refund;
- PayRegister refund;
- cashback;
- rewards;
- bug bounty payout;
- partner payout;
- testnet/signet faucet.

Security rules:

- Valuable withdraw requests require auth before QR issuance.
- Policy approval is required before withdraw QR generation.
- `k1` must be single-use.
- Amount limits are required.
- Cooldowns are required for high-risk payouts.
- Audit event is required.
- Payout must be asynchronous and observable.
- Withdraw cannot be used as authentication by itself.

## 11. LNURL-verify decision

Bastion must verify settlement before issuing entitlements.

Supported verification methods:

- LNURL-verify URL if available;
- internal Lightning node settlement status;
- BTCPay / provider confirmation;
- payment preimage verification where available.

Rules:

- Invoice issued is not payment proof.
- `settled=true` is required before entitlement issuance.
- Duplicate settlement callback must be idempotent.
- Expired invoice cannot issue entitlement.
- Verify checks must be audited.

## 12. successAction decision

`successAction` will be used for post-payment UX.

Allowed use cases:

- “Pro Pass activated”;
- activation link;
- receipt link;
- Bastion Vault setup link;
- PayRegister receipt link;
- Business onboarding link.

Security rules:

- `successAction` URL must not contain raw Access Pass.
- `successAction` URL must not contain raw session token.
- `successAction` URL must not contain recovery material.
- `successAction` URL must use a short-lived activation reference.
- Activation endpoint must still check payment/entitlement state.

## 13. commentAllowed decision

`commentAllowed` may be supported only as untrusted user metadata.

Allowed use cases:

- invoice note;
- merchant order reference;
- receipt comment;
- support reference.

Forbidden:

- authorization;
- entitlement granting;
- role assignment;
- recovery;
- policy bypass;
- identity verification.

## 14. payerData decision

`payerData` may be supported with privacy-first defaults.

Allowed by default:

- `auth`.

Optional / disabled by default:

- `identifier`;
- `pubkey`;
- `name`;
- `email`.

Rules:

- `payerData.email` must not be mandatory.
- `payerData.name` must not be mandatory.
- `payerData.identifier` must not become global `user_id`.
- `payerData.auth` is preferred over personal identity.
- `payerData` must be stored minimally.
- `payerData` must be subject to retention policy.

## 15. Domain stability decision

The LNURL-auth domain is security-sensitive and must be stable.

Rules:

- `auth.bitcoin-bastion.com` must be treated as stable auth domain.
- Changing auth domain can create new wallet-derived accounts.
- Domain migration must require explicit account/principal linking flow.
- Merchant auth subdomains must be versioned.
- Custom merchant domains require documented domain policy.

## 16. Principal model decision

The principal layer must support:

```text
Principal
├── BitcoinWalletPrincipal
└── LightningWalletPrincipal
```

BitcoinWalletPrincipal fields:

- `principal_hash`;
- `address_hash`;
- `script_pubkey_hash`;
- `network`;
- `proof_method`;
- `verification_strength`;
- `status`;
- `created_at`;
- `last_verified_at`.

LightningWalletPrincipal fields:

- `principal_hash`;
- `lnurl_key_hash`;
- `auth_domain`;
- `proof_method`;
- `verification_strength`;
- `status`;
- `created_at`;
- `last_verified_at`.

Rules:

- No raw Bitcoin address as `user_id`.
- No raw LNURL key as `user_id`.
- No global `user_id` by default.
- Per-product pseudonyms should be supported.
- No email/KYC requirement.

## 17. Policy Engine decision

Policy Engine must support these actor types:

- `bitcoin_wallet_principal`;
- `lightning_wallet_principal`;
- `wallet_device`;
- `access_certificate`;
- `child_api_key`;
- `business_role`;
- `payregister_device`;
- `bot`.

Policy Engine must support these auth methods:

- `bip322`;
- `legacy_message_signature`;
- `lnurl_auth`;
- `access_certificate`;
- `hardware_wallet`;
- `air_gapped`;
- `multisig_quorum`.

Policy Engine must support these payment methods:

- `lnurl_pay`;
- `lightning_address`;
- `btcpay`;
- `lightning_invoice`;
- `onchain_btc`;
- `manual_grant`.

Policy Engine must support this withdraw method:

- `lnurl_withdraw`.

Policy checks:

- principal active;
- device active;
- session active;
- wallet proof freshness;
- LNURL `k1` validity;
- verification strength;
- subscription tier;
- scopes;
- metric group;
- quota;
- object access;
- business role;
- PayRegister role;
- risk level;
- revocation state;
- recovery state;
- step-up requirement;
- multi-wallet quorum requirement.

## 18. Audit decision

Audit Chain must include wallet and LNURL events.

Wallet events:

- `wallet_challenge_created`;
- `wallet_registration_success`;
- `wallet_registration_failed`;
- `wallet_login_success`;
- `wallet_login_failed`;
- `wallet_device_bound`;
- `wallet_session_created`;
- `wallet_step_up_required`;
- `wallet_step_up_success`;
- `wallet_step_up_failed`;
- `wallet_principal_revoked`;
- `wallet_recovery_started`;
- `wallet_recovery_completed`.

LNURL events:

- `lnurl_auth_challenge_created`;
- `lnurl_auth_callback_success`;
- `lnurl_auth_callback_failed`;
- `lnurl_auth_k1_reused`;
- `lnurl_auth_k1_expired`;
- `lnurl_pay_request_created`;
- `lnurl_invoice_issued`;
- `lnurl_invoice_settled`;
- `lnurl_verify_success`;
- `lnurl_verify_failed`;
- `lnurl_payment_proof_created`;
- `lnurl_entitlement_issued`;
- `lightning_address_resolved`;
- `lnurl_withdraw_request_created`;
- `lnurl_withdraw_invoice_received`;
- `lnurl_withdraw_paid`;
- `lnurl_withdraw_failed`;
- `lnurl_payerdata_received`;
- `lnurl_success_action_created`.

Rules:

- No raw address in audit.
- No raw LNURL key in audit.
- No raw signature in audit.
- No raw `k1` in audit if avoidable.
- No raw session token in audit.
- Use hashes/fingerprints only.
- Maintain audit hash chain.

## 19. Revocation decision

Revocation Registry must cover these wallet targets:

- `wallet_principal`;
- `wallet_proof`;
- `wallet_device`;
- `wallet_session`;
- `wallet_step_up_proof`;
- `wallet_bound_entitlement`;
- `wallet_recovery_capsule`;
- `multi_wallet_quorum`.

Revocation Registry must cover these LNURL targets:

- `lnurl_principal`;
- `lnurl_auth_key`;
- `lnurl_auth_challenge`;
- `lnurl_k1`;
- `lnurl_payment_request`;
- `lnurl_payment_proof`;
- `lnurl_withdraw_request`;
- `lightning_address`;
- `payregister_lnurl_terminal`.

Revocation Registry must cover these Access targets:

- `access_certificate`;
- `delegated_pass`;
- `child_api_key`;
- `offline_validity_pack`.

## 20. Recovery decision

Recovery must use Recovery Capsule, not password reset.

Recovery factors may include:

- BIP-322 wallet proof;
- LNURL-auth fresh proof;
- trusted device history;
- recovery file;
- payment proof;
- owner wallet;
- admin wallet;
- hardware wallet proof;
- recovery capsule;
- transparency checkpoint;
- cooldown.

Forbidden recovery factors:

- Bitcoin seed;
- Bitcoin private key;
- wallet mnemonic;
- support-only reset;
- email-only reset;
- invoice-only reset;
- LNURL-auth alone for high-value recovery.

Rules:

- LNURL-auth may be one recovery factor, not the whole recovery for Pro/Business/Enterprise/Sovereign.
- Recovery must never be easier than login.
- Recovery must be audited.
- Recovery must be policy-gated.

## 21. Access Certificate bridge decision

Access Certificate remains an optional high-assurance layer.

Bridge:

```text
Wallet Principal
or Lightning Principal
→ optional Access Certificate
→ optional bastion-pass.bbp
→ optional Access Vault
→ optional Offline Validity Pack
```

Use cases:

- Pro automation;
- Business roles;
- Enterprise policy;
- Sovereign mode;
- PayRegister local mode;
- delegated passes;
- offline validity packs;
- PQ issuer signatures;
- recovery quorum.

Rules:

- Access Certificate must not be bearer access.
- LNURL-auth must not weaken Access Certificate checks.
- Access Certificate must remain bound to principal/device/policy.

## 22. PQ decision

Post-quantum support applies to Bastion-issued objects, not to Bitcoin/LNURL wallet signatures themselves.

PQ-ready objects:

- subscription entitlement;
- access certificate;
- recovery capsule;
- revocation epoch;
- transparency checkpoint;
- offline validity pack;
- delegated pass;
- policy checkpoint.

Rules:

- Do not claim ML-KEM/ML-DSA/SLH-DSA are implemented unless real implementation exists.
- Include `crypto_epoch` and `signature_suite` metadata.
- Current wallet proofs remain classical unless the wallet ecosystem supports something else.
- PQ issuer chain is a crypto-agility and long-term hardening layer.

## 23. Privacy decision

Privacy-first design is mandatory.

Rules:

- HMAC-SHA256 lookup identifiers;
- separate Wallet Auth DB;
- separate LNURL Auth DB;
- separate Payment DB;
- separate Usage DB;
- separate PayRegister DB;
- no global `user_id` by default;
- per-product pseudonyms;
- short retention windows;
- no KYC by default;
- no mandatory email;
- minimal `payerData`;
- dedicated auth address recommendation;
- cold treasury wallet warning.

Required user-facing warning:

> Use a dedicated Bastion auth wallet/address. Do not use your cold treasury wallet for routine login. Bastion will never ask for your Bitcoin seed.

## 24. API surface decision

Future API areas:

Wallet Auth:

```text
POST /v1/wallet-auth/challenges
POST /v1/wallet-auth/register
POST /v1/wallet-auth/login
POST /v1/wallet-auth/sessions
POST /v1/wallet-auth/step-up
GET  /v1/wallet-auth/me
GET  /v1/wallet-auth/entitlements
GET  /v1/wallet-auth/devices
POST /v1/wallet-auth/recovery/start
POST /v1/wallet-auth/recovery/complete
POST /v1/wallet-auth/lockdown
```

LNURL:

```text
POST /v1/lnurl/auth/challenges
GET  /v1/lnurl/auth/callback
POST /v1/lnurl/auth/sessions
POST /v1/lnurl/auth/step-up
```

LNURL Pay:

```text
POST /v1/lnurl/pay/subscriptions
GET  /v1/lnurl/pay/callback/{payment_id}
GET  /v1/lnurl/pay/verify/{payment_id}
```

Lightning Address:

```text
GET /.well-known/lnurlp/{name}
```

LNURL Withdraw:

```text
POST /v1/lnurl/withdraw/requests
GET  /v1/lnurl/withdraw/callback/{withdraw_id}
```

PayRegister LNURL:

```text
POST /v1/payregister/lnurl/payments
GET  /v1/payregister/.well-known/lnurlp/{store_or_terminal}
POST /v1/payregister/lnurl/refunds
```

These are future surfaces only. This ADR does not add routes.

## 25. Consequences

Positive:

- wallet-first registration without email/password;
- Lightning-native login UX;
- Lightning-native subscription checkout;
- human-readable Lightning Address payments;
- PayRegister-ready payment UX;
- controlled refund/payout layer;
- stronger separation of identity, payment, device, session, and policy;
- better mobile UX;
- optional high-assurance bridge for Pro/Business/Enterprise;
- PQ-ready issuer chain for Bastion-issued credentials.

Negative:

- more complex architecture;
- LNURL domain stability requirements;
- wallet compatibility risk;
- LNURL-auth is not on-chain ownership proof;
- `payerData` privacy risk;
- withdraw `k1` theft risk if not policy-gated;
- more API surface;
- more test and release-gate burden.

Mitigations:

- keep BIP-322 for Bitcoin ownership proof;
- keep LNURL-auth for Lightning-native login/step-up;
- require PoP sessions for protected API;
- require Policy Engine for all protected access;
- require settlement verification before entitlements;
- require auth/policy before withdraw QR issuance;
- use HMAC identifiers and DB separation;
- add wallet compatibility registry;
- add release gates.

## 26. Non-goals

This ADR does not implement:

- runtime code;
- database models;
- migrations;
- SDKs;
- frontend;
- real BIP-322 verifier;
- real LNURL verifier;
- real Lightning node integration;
- real ML-KEM/ML-DSA/SLH-DSA;
- custody;
- Bitcoin transaction signing;
- wallet seed handling;
- password fallback.

Explicitly not goals:

- custody of user funds;
- storing Bitcoin private keys;
- storing wallet seed phrases;
- using Lightning Address as identity;
- using LNURL-auth as treasury proof;
- using LNURL-withdraw without policy;
- using `payerData.email` as mandatory identity.

## 27. Implementation roadmap

0/72 Wallet-first migration audit
1/72 Wallet-first + LNURL ADR
2/72 Wallet-first + LNURL threat model
3/72 Wallet + LNURL auth domain package
4/72 Wallet + LNURL schemas
5/72 Wallet + LNURL DB models
6/72 Wallet + LNURL Alembic migration
7/72 Wallet privacy commitments
8/72 Structured Bastion Auth Intent
9/72 Wallet challenge service
10/72 Wallet proof verifier interface
11/72 BIP-322 verifier
12/72 Legacy Bitcoin message signature fallback
13/72 Hardware wallet proof metadata
14/72 Wallet compatibility registry
15/72 Wallet Principal service
16/72 Wallet device binding service
17/72 Wallet session service
18/72 Wallet PoP request verifier
19/72 Bastion LNURL domain package
20/72 LNURL encoding / decoding / URL safety
21/72 LNURL k1 registry and replay protection
22/72 LNURL-auth challenge service
23/72 LNURL-auth callback verifier
24/72 Lightning Principal service
25/72 LNURL-auth session bridge
26/72 LNURL-auth step-up service
27/72 LNURL-auth audit events
28/72 LNURL-pay subscription request service
29/72 LNURL-pay metadata builder
30/72 LNURL-pay callback invoice service
31/72 LNURL-verify settlement service
32/72 LNURL payment proof service
33/72 LNURL payment → subscription entitlement binding
34/72 LNURL successAction activation service
35/72 LNURL commentAllowed handling
36/72 LNURL payerData.auth binding
37/72 Lightning Address service
38/72 /.well-known/lnurlp routes
39/72 Product Lightning Addresses
40/72 PayRegister LNURL-pay static QR
41/72 PayRegister cashier / shift metadata
42/72 Merchant Lightning Address
43/72 LNURL receipt packet
44/72 LNURL-withdraw request service
45/72 LNURL-withdraw callback verifier
46/72 Refund / payout policy integration
47/72 PayRegister refund via LNURL-withdraw
48/72 Withdraw audit and risk limits
49/72 Wallet-bound Subscription Entitlements
50/72 Lightning Principal policy actor types
51/72 LNURL Policy Engine hooks
52/72 Wallet + LNURL Step-Up policy
53/72 Wallet + LNURL Revocation extensions
54/72 Wallet + LNURL Audit Chain events
55/72 Access Integrity Score 2.0 with LNURL signals
56/72 Wallet + LNURL observability metrics
57/72 Recovery Capsule foundation
58/72 LNURL-auth as recovery factor
59/72 Multi-wallet / multi-method quorum
60/72 Access Certificate bridge for wallet/LNURL principals
61/72 Offline validity pack bridge
62/72 PQ issuer metadata for LNURL-bound objects
63/72 Transparency checkpoints for wallet/LNURL auth
64/72 Wallet Auth API router
65/72 LNURL API router
66/72 Wallet + LNURL auth dependencies
67/72 Python SDK wallet + LNURL auth
68/72 TypeScript SDK wallet + LNURL auth
69/72 CLI wallet + LNURL auth
70/72 Frontend wallet + LNURL auth flow
71/72 Reflex wallet + LNURL auth flow
72/72 Final Wallet-first + LNURL production release gate

## 28. Acceptance criteria

- [x] `docs/ADR_WALLET_FIRST_LNURL_PROOF_OF_ACCESS_AUTH.md` exists.
- [x] ADR states wallet-first is primary.
- [x] ADR states LNURL is Lightning-native adapter layer.
- [x] ADR states LNURL-auth is not full authorization.
- [x] ADR states LNURL-pay invoice issuance is not settlement.
- [x] ADR states LNURL-withdraw must be policy-gated.
- [x] ADR states Lightning Address is not identity.
- [x] ADR states Access Certificate remains optional high-assurance layer.
- [x] ADR states no Bitcoin seed/private key for auth or recovery.
- [x] ADR states no password fallback.
- [x] ADR states no bearer Access Pass.
- [x] ADR includes principal model.
- [x] ADR includes Policy Engine requirements.
- [x] ADR includes Audit/Revocation requirements.
- [x] ADR includes privacy requirements.
- [x] ADR includes PQ limitations truthfully.
- [x] ADR includes 0/72 implementation roadmap.
- [x] No runtime code was changed.
- [x] No database models were added.
- [x] No migrations were added.
- [x] No fake implementation claims were added.
