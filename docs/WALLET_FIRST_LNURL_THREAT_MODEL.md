# Wallet-first + LNURL Proof-of-Access Auth PQ v2 Threat Model

Prompt: **2/72 — Wallet-first + LNURL Threat Model**. Scope: documentation and security analysis only. This document adds no runtime code, database models, migrations, API routes, SDK changes, frontend behavior, fake BIP-322 implementation, fake LNURL implementation, or fake PQ implementation.

## 1. Executive Summary

This threat model identifies production security risks for Bastion Wallet-first Proof-of-Access Auth PQ v2 with the integrated Bastion LNURL Layer. It is intended to drive concrete implementation work from Prompt 3/72 onward and to define release-gate failures for Prompt 72/72.

The system replaces classic account-based authentication with:

- Bitcoin wallet proof;
- Lightning wallet proof through LNURL-auth;
- Wallet Principal / Lightning Principal;
- Device Binding;
- Proof-of-Possession Session;
- Policy Engine;
- Revocation Registry;
- Audit Chain;
- optional Access Certificate;
- optional PQ-ready issuer chain for Bastion-issued objects.

The design explicitly rejects:

- password login;
- mandatory email login;
- bearer Access Pass;
- Bitcoin seed/private key usage;
- support-only recovery;
- wallet signature as full authorization;
- Lightning Address as identity;
- LNURL-pay invoice creation as payment proof;
- LNURL-withdraw without policy gating.

Core security law:

- Wallet-first is not wallet-only.
- LNURL-native is not LNURL-only.
- Wallet proof proves wallet control.
- LNURL-auth proves Lightning wallet control.
- Device Key proves continuity.
- PoP Session proves request possession.
- Subscription Entitlement defines allowed API surface.
- Policy Engine gives final authorization.
- Audit Chain proves history.
- Revocation Registry limits damage.
- Access Certificate remains optional high-assurance hardening layer.

## 2. Assets

| Asset name | Sensitivity | Why it matters | Primary threat | Required protection |
|---|---:|---|---|---|
| Wallet Principal | Critical | Primary wallet-first actor. | Account takeover/correlation. | HMAC identifiers, revocation, policy checks. |
| BitcoinWalletPrincipal | Critical | Represents verified Bitcoin wallet control. | Wrong proof/network or address leak. | BIP-322, network binding, no raw address ids. |
| LightningWalletPrincipal | Critical | Represents verified LNURL-auth control. | Linking-key replay/tracking. | Domain binding, HMAC key hash, revocation. |
| `principal_hash` | High | Lookup handle for principal. | Correlation across products. | Domain-separated HMAC, pseudonyms. |
| `address_hash` | High | Private address lookup. | Deanonymization. | HMAC-SHA256 with pepper; no raw logs. |
| `lnurl_key_hash` | High | LNURL-auth key lookup. | Tracking/global identifier. | HMAC, per-product alias, DB separation. |
| `script_pubkey_hash` | High | Script-level wallet proof lookup. | Address/script leakage. | Hash only; network separation. |
| Device Key | Critical | Proves device continuity/request possession. | Device takeover. | Public key fingerprint, attestation metadata, revocation. |
| Device Binding | Critical | Links principal to trusted device. | Malicious device binding. | Fresh proof, step-up, audit, revocation. |
| PoP Session | Critical | Short-lived access vehicle. | Session theft/replay. | TTL, nonce, request signature, revocation. |
| Session token | Critical | Session lookup secret. | Bearer-like misuse/leakage. | Hash at rest, never log, short TTL. |
| Session signing key | Critical | Signs requests. | Request forgery. | Client custody, rotation, no backend private key storage. |
| Request nonce | High | Replay prevention. | Replayed request accepted. | Unique nonce registry, timestamp skew checks. |
| Wallet Auth Challenge | High | Wallet-proof challenge. | Blind signing/phishing/replay. | Structured intent, TTL, hash, action binding. |
| Structured Bastion Auth Intent | High | Human-readable signed intent. | User signs hidden action. | Canonicalization, display text, policy hash. |
| LNURL k1 challenge | Critical | LNURL-auth/withdraw nonce. | Replay/guess/unknown k1 accepted. | 32 random bytes, hash store, TTL, single-use. |
| LNURL-auth callback | Critical | Auth verifier endpoint. | Forged callback/signature. | Expected k1, DER ECDSA verify, action/domain binding. |
| LNURL-pay request | High | Payment intent metadata. | Plan/amount tampering. | Canonical metadata hash, min/max/exact amount policy. |
| LNURL-pay invoice | High | Payment request to wallet. | Invoice treated as settled. | Settlement verification gate. |
| LNURL payment proof | Critical | Settlement evidence for entitlement. | Duplicate/fake proof. | Provider/internal verification, idempotency, audit. |
| LNURL-verify result | Critical | Entitlement gate signal. | False settlement. | Trusted verifier, status mapping, idempotent checks. |
| LNURL-withdraw request | Critical | Payout/refund authorization. | Unauthorized payout. | Policy before QR, state machine, amount limits. |
| LNURL-withdraw k1 | Critical | Claim token for payout. | Theft/replay. | Single-use, TTL, auth before QR for valuable payouts. |
| Lightning Address records | Medium | Payment routing registry. | Identity confusion/enumeration. | Minimal public metadata, domain policy. |
| `payerData` | High | Optional payer metadata. | Privacy leakage/profile building. | Minimal fields, no mandatory email/name, retention. |
| `successAction` activation reference | High | Post-payment activation UX. | Secret leakage/access bypass. | Short-lived reference, state checks, no raw secrets. |
| Subscription Entitlement | Critical | Defines allowed API surface. | Unauthorized premium access. | Issuer signature, settlement gate, policy checks. |
| Metric Entitlement | High | Controls paid metric groups/quotas. | Metric bypass. | Policy enforcement, quota tracking. |
| Policy Decision | Critical | Final authorization result. | Bypass/stale decision. | Fresh evaluation, signed/audited decision context. |
| Revocation Registry entry | Critical | Limits blast radius. | Revoked entity still works. | Query on every protected path; epochs. |
| Audit Chain event | High | Evidence/history. | Tampering/missing failures. | Hash chain, mandatory events, redaction. |
| Recovery Capsule | Critical | Recovery authority. | Recovery takeover/leakage. | Quorum, encryption, cooldown, audit. |
| Access Certificate | Critical | Optional high-assurance credential. | Bearer misuse. | Bind to principal/device/policy; no bearer semantics. |
| Offline Validity Pack | Critical | Offline trust bundle. | Stale/revoked offline access. | Revocation epoch, expiry, signature suite. |
| PayRegister terminal context | High | Merchant payment/refund context. | Terminal spoofing/refund abuse. | Terminal hash, shift binding, policy. |
| Business role binding | High | Role authorization. | Privilege escalation. | Owner/admin step-up, object-level policy. |
| Issuer signing keys | Critical | Signs Bastion-issued objects. | Credential forgery. | HSM/secret manager, rotation, audit. |
| Server pepper | Critical | HMAC lookup protection. | Hash reversal/correlation. | Secret manager, rotation plan, never log. |
| Wallet compatibility registry | Medium | Determines supported proof paths. | Unsafe wallet mode allowed. | Signed registry, policy constraints. |
| Transparency checkpoint | High | Tamper evidence/long-term integrity. | Hidden history rewrite. | Hash checkpointing, audit, publication policy. |

## 3. Trust Boundaries

| Boundary | Trusted side | Untrusted side | Attack surface | Required validation |
|---|---|---|---|---|
| User wallet ↔ browser/frontend | Wallet key custody | Browser DOM/network/user input | Phishing, malicious JS, wrong intent display | Structured intent, clear warnings, no seed/private key fields. |
| User wallet ↔ LNURL endpoint | Wallet signature engine | Public LNURL URL/callback | k1 phishing/replay/domain confusion | Expected k1, domain/action binding, signature verify. |
| Browser/frontend ↔ backend API | Backend API | Browser/client network | Tampered requests, token leakage | TLS, schema validation, PoP headers, policy. |
| Lightning wallet ↔ LNURL-auth callback | Backend verifier | Lightning wallet/client | Forged callback, CORS quirks, replay | DER signature verify, k1 registry, GET compatibility. |
| Lightning wallet ↔ LNURL-pay callback | Backend invoice issuer | Wallet/user callback params | Amount/metadata tamper | Canonical metadata, amount validation, no entitlement. |
| Lightning wallet ↔ LNURL-withdraw callback | Backend payout service | Wallet invoice callback | Stolen k1, oversized invoice | k1 single-use, amount bounds, state machine. |
| Backend ↔ Lightning node / BTCPay / payment provider | Backend policy/entitlement code | External provider | False settlement, webhook replay | Provider signatures, internal status, idempotency. |
| Backend ↔ database | Application code | DB/storage boundary | Injection, leakage, stale state | ORM validation, encryption where needed, least privilege. |
| Backend ↔ Policy Engine | Policy engine | Route/service caller | Policy bypass/malformed context | Required dependencies, typed context, deny by default. |
| Backend ↔ Audit Chain | Audit chain service | Event producer | Missing/forged events | Canonical events, hash chain, mandatory events. |
| Backend ↔ Revocation Registry | Revocation registry | Session/principal services | Revoked target ignored | Central check, target enums, revocation epoch. |
| Backend ↔ SDK clients | Backend API | Third-party SDK apps | Bearer fallback/logging secrets | SDK redaction, no bearer Access Pass, PoP signing. |
| PayRegister terminal ↔ backend | Backend policy/payment service | Terminal/local operator | Terminal spoofing, stale QR/refund | Terminal hash, shift, policy, revocation. |
| PayRegister terminal ↔ local network | Terminal app | LAN/NFC/QR scanners | QR replay/MITM/local compromise | Signed payloads, TLS, terminal attestation where possible. |
| Business operator ↔ business workspace | Policy/workspace config | Operator browser/device | Role escalation/refund abuse | Business role policy, owner/admin step-up. |
| Recovery participant ↔ recovery service | Recovery policy service | Participant proof/input | Support-only/email-only/seed capture | Factor policy, no seed fields, cooldown, audit. |
| Issuer key provider ↔ certificate/entitlement issuer | Key provider/HSM | Issuer service integration | Key misuse/rotation gaps | Key IDs, crypto_epoch, rotation audit, least privilege. |

## 4. Security Invariants

1. Wallet proof alone must not grant full protected API access.
2. LNURL-auth alone must not grant full protected API access.
3. Device Binding is required for persistent or trusted access.
4. PoP Session is required for protected API access.
5. Policy Engine must decide every protected request.
6. Access Pass / Access Certificate must not be bearer access.
7. Bitcoin address must not become public `user_id`.
8. Lightning Address must not become identity by itself.
9. LNURL-auth linking key must not be treated as on-chain treasury ownership proof.
10. LNURL-pay invoice creation must not issue entitlement.
11. Entitlement issuance requires verified settlement.
12. LNURL-withdraw QR for valuable payout requires auth and policy before QR issuance.
13. `payerData.email` must not be mandatory by default.
14. `commentAllowed` must never authorize access.
15. `successAction` URL must not contain raw pass/session/recovery data.
16. `k1` must be single-use.
17. Used `k1` must be marked used or removed.
18. Unexpected `k1` must be rejected.
19. Recovery must never be easier than login/session verification.
20. Bitcoin seed/private key/mnemonic must never be accepted.
21. No backend private keys for user wallets.
22. No support-only recovery.
23. No fake PQ implementation claims.

## 5. Threat Table Format

Every threat below uses this format:

| ID | Threat | Scenario | Impact | Likelihood | Severity | Affected Assets | Mitigation | Required Tests | Implementation Prompts |
| -- | ------ | -------- | ------ | ---------- | -------- | --------------- | ---------- | -------------- | ---------------------- |

Severity scale: Low, Medium, High, Critical. Likelihood scale: Low, Medium, High.

## 6. Wallet-first Threats

| ID | Threat | Scenario | Impact | Likelihood | Severity | Affected Assets | Mitigation | Required Tests | Implementation Prompts |
| -- | ------ | -------- | ------ | ---------- | -------- | --------------- | ---------- | -------------- | ---------------------- |
| WALLET-01 | Wallet signature treated as full authorization | Wallet signature immediately grants premium API access without Device Key, PoP Session, or Policy Engine. | Full account/API takeover. | Medium | Critical | Wallet Principal, PoP Session, Policy Decision | Wallet proof only creates/verifies principal; Device Binding, PoP Session and Policy Engine are mandatory. | Wallet signature alone cannot access protected endpoint; policy is called for protected access. | Prompt 8/72, Prompt 18/72, Prompt 51/72, Prompt 72/72 |
| WALLET-02 | Blind wallet signature phishing | User signs opaque challenge that approves high-risk action. | High-risk action abuse. | High | High | Wallet Auth Challenge, Structured Auth Intent | Structured Bastion Auth Intent; human-readable action; warnings; critical actions require human intent fields. | Intent text is canonical; opaque challenge rejected for critical action. | Prompt 8/72, Prompt 52/72, Prompt 72/72 |
| WALLET-03 | Bitcoin address becomes `user_id` | Backend stores/exposes raw address as global account id. | Privacy leak/correlation. | Medium | High | address_hash, principal_hash | HMAC-SHA256 `address_hash`, `principal_hash`, per-product pseudonyms, no global `user_id`. | Raw address not in public schemas/logs; no global user id. | Prompt 7/72, Prompt 15/72, Prompt 72/72 |
| WALLET-04 | Cold treasury wallet used for routine login | User repeatedly signs routine logins with cold storage wallet. | Treasury exposure/phishing. | Medium | High | BitcoinWalletPrincipal, Wallet Auth Challenge | Dedicated Auth Address Mode; UI warning; treasury wallet only for ownership/recovery/high-risk approval. | Warning copy required; routine login discourages treasury context. | Prompt 7/72, Prompt 70/72, Prompt 71/72 |
| WALLET-05 | Wrong network proof accepted | Testnet/signet/regtest proof accepted for mainnet access. | Unauthorized access/confusion. | Medium | High | BitcoinWalletPrincipal, Wallet Proof | Network separation; intent includes network; verifier checks network. | Mainnet rejects testnet/signet proofs. | Prompt 10/72, Prompt 11/72, Prompt 72/72 |
| WALLET-06 | Legacy signature used for high-risk action | Compatibility fallback approves recovery, treasury, or Enterprise policy change. | High-risk privilege escalation. | Medium | Critical | Wallet Proof, Policy Decision, Recovery Capsule | Legacy signatures low-risk only; BIP-322/high-assurance proof required; Policy Engine enforces strength. | Legacy signature denied for high-risk action. | Prompt 12/72, Prompt 51/72, Prompt 72/72 |
| WALLET-07 | Hardware assurance falsely claimed | Client claims hardware-wallet proof without evidence. | Misclassified trust level. | Medium | High | Wallet Proof, compatibility registry | Hardware metadata is not assurance; only verified attestation/policy evidence increases strength. | Self-claimed hardware not high assurance. | Prompt 13/72, Prompt 14/72, Prompt 51/72 |
| WALLET-08 | Device takeover after wallet login | Attacker logs in once and binds malicious device. | Persistent unauthorized access. | Medium | Critical | Device Binding, Device Key, Wallet Principal | New device requires fresh proof; risk scoring; audit; revocation; step-up for `device_add`. | Device add requires fresh proof/step-up. | Prompt 16/72, Prompt 52/72, Prompt 53/72 |
| WALLET-09 | PoP session replay | Attacker reuses request with same nonce/timestamp/signature. | Request replay/data abuse. | Medium | Critical | PoP Session, request nonce | Nonce registry; timestamp freshness; body hash; request signature verification. | Duplicate nonce rejected; old timestamp rejected. | Prompt 18/72, Prompt 72/72 |
| WALLET-10 | Principal correlation across products | Same principal links API, PayRegister, Desktop AI, and other services. | Cross-product tracking. | High | High | principal_hash, usage/payment DBs | Per-product pseudonyms; DB separation; short retention; no global `user_id`. | Product pseudonyms differ; direct joins blocked. | Prompt 7/72, Prompt 15/72, Prompt 36/72 |

## 7. LNURL-auth Threats

| ID | Threat | Scenario | Impact | Likelihood | Severity | Affected Assets | Mitigation | Required Tests | Implementation Prompts |
| -- | ------ | -------- | ------ | ---------- | -------- | --------------- | ---------- | -------------- | ---------------------- |
| LNURLAUTH-01 | k1 replay | Attacker reuses LNURL-auth k1 after successful login. | Account/session takeover. | High | Critical | LNURL k1, LNURL-auth callback | 32-byte random k1; single-use registry; short expiry; mark used/delete; audit reuse. | Reused k1 rejected/audited. | Prompt 21/72, Prompt 23/72, Prompt 72/72 |
| LNURLAUTH-02 | Unexpected k1 accepted | Callback accepts k1 never issued. | Forged auth. | Medium | Critical | LNURL k1, callback | Only expected k1 accepted; lookup required; unknown rejected. | Unknown k1 rejected. | Prompt 21/72, Prompt 23/72 |
| LNURLAUTH-03 | Expired k1 accepted | Wallet signs old auth request. | Replay/auth bypass. | Medium | High | LNURL k1 | TTL enforcement; expiry check; audit expired callback. | Expired k1 rejected. | Prompt 21/72, Prompt 23/72 |
| LNURLAUTH-04 | k1 not bound to action | Login k1 reused for high-risk action. | Step-up bypass. | Medium | Critical | LNURL k1, Policy Decision | k1 bound to action and policy intent; mismatch rejected. | Wrong action k1 rejected. | Prompt 21/72, Prompt 22/72, Prompt 52/72 |
| LNURLAUTH-05 | k1 not bound to domain | Challenge for one domain accepted on another. | Domain confusion/principal split. | Medium | High | LNURL k1, Lightning Principal | Domain binding; stable auth domain; domain policy. | Wrong domain rejected. | Prompt 21/72, Prompt 22/72, Prompt 23/72 |
| LNURLAUTH-06 | LNURL-auth used as treasury proof | System treats LNURL linking key as on-chain ownership proof. | Treasury authorization bypass. | Medium | Critical | Lightning Principal, treasury policy | LNURL-auth = Lightning login/step-up only; BIP-322/descriptor proof required for treasury ownership. | LNURL-auth denied for treasury ownership proof. | Prompt 17/72, Prompt 51/72, Prompt 72/72 |
| LNURLAUTH-07 | Auth domain migration breaks principals | Domain change creates duplicate wallet-derived accounts. | Account loss/duplication. | Medium | High | Lightning Principal | Stable auth domain; versioned migration; explicit principal linking flow. | Domain migration requires link proof. | Prompt 15/72, Prompt 24/72, Prompt 42/72 |
| LNURLAUTH-08 | Callback CORS/browser-wallet incompatibility | Browser wallets fail due to missing GET/CORS behavior. | Login failure/workaround pressure. | Medium | Medium | LNURL-auth callback | GET endpoints support wallet compatibility; state changes still require k1/policy. | Browser wallet callback contract tests. | Prompt 20/72, Prompt 23/72, Prompt 65/72 |
| LNURLAUTH-09 | Linking key becomes tracking id | LNURL key hash reused across products. | Cross-product tracking. | High | High | lnurl_key_hash | HMAC lookup, per-product alias, separate LNURL Auth DB, no raw key logging. | Product alias separation; raw key redaction. | Prompt 7/72, Prompt 24/72, Prompt 36/72 |
| LNURLAUTH-10 | LNURL-auth step-up bypass | High-risk action proceeds without fresh LNURL-auth proof. | Privilege escalation. | Medium | Critical | Policy Decision, LNURL k1 | Policy returns `step_up_required`; fresh action=auth challenge; audit step-up. | Step-up required for sensitive action. | Prompt 26/72, Prompt 52/72, Prompt 72/72 |

## 8. LNURL-pay Threats

| ID | Threat | Scenario | Impact | Likelihood | Severity | Affected Assets | Mitigation | Required Tests | Implementation Prompts |
| -- | ------ | -------- | ------ | ---------- | -------- | --------------- | ---------- | -------------- | ---------------------- |
| LNURLPAY-01 | Invoice generated treated as settled | Entitlement issued after invoice creation before payment. | Free premium access. | High | Critical | LNURL invoice, Entitlement | Invoice issued is not payment proof; settlement required; `settled=true` required. | Invoice creation does not issue entitlement. | Prompt 31/72, Prompt 33/72, Prompt 72/72 |
| LNURLPAY-02 | Duplicate callback creates duplicate entitlement | Repeated callback/webhook issues multiple entitlements. | Double grant/account inconsistency. | Medium | High | Payment proof, Entitlement | Idempotent proof creation; unique payment/invoice hash; audit duplicates. | Duplicate callback idempotent. | Prompt 32/72, Prompt 33/72 |
| LNURLPAY-03 | Metadata tampering | User sees one plan but backend issues another. | Wrong plan/fraud. | Medium | High | LNURL-pay request | Canonical metadata hash; plan code bound to request; audit; policy validates entitlement. | Metadata hash mismatch rejected. | Prompt 28/72, Prompt 29/72, Prompt 54/72 |
| LNURLPAY-04 | Amount mismatch | Invoice amount differs from selected plan. | Underpayment/overcharge. | Medium | High | LNURL invoice | Min/max validation; exact amount policy; callback validates `amount_msat`. | Wrong amount rejected. | Prompt 28/72, Prompt 30/72, Prompt 31/72 |
| LNURLPAY-05 | commentAllowed used as authority | Comment grants plan, role, or support override. | Authorization bypass. | Medium | Critical | commentAllowed, Policy Decision | Untrusted metadata only; never authorization. | Comment cannot grant access/role. | Prompt 35/72, Prompt 51/72, Prompt 72/72 |
| LNURLPAY-06 | payerData.email mandatory | LNURL-pay requires email, recreating account auth. | Privacy/product regression. | Medium | High | payerData | Email disabled by default; `payerData.auth` preferred; no mandatory personal fields. | Email not required by default. | Prompt 36/72, Prompt 72/72 |
| LNURLPAY-07 | payerData.auth links too much | Payment, auth, and usage permanently correlated. | Privacy leak. | High | High | payerData, Payment DB, Usage DB | Minimal payerData; DB separation; retention; per-product pseudonyms. | No direct auth/payment/usage join by raw id. | Prompt 7/72, Prompt 36/72 |
| LNURLPAY-08 | successAction leaks token | Activation URL contains Access Pass, session, or recovery material. | Secret compromise. | Medium | Critical | successAction reference | Short-lived activation ref; no raw secrets; activation endpoint checks state. | URL contains no raw secrets; expired ref denied. | Prompt 34/72, Prompt 72/72 |
| LNURLPAY-09 | Paid invoice but verify unavailable | Verify unavailable leaves entitlement uncertain. | Access delay/support pressure. | Medium | Medium | Verify result, Entitlement | Internal node/provider fallback; pending state; retry; no entitlement until verified. | Pending verify does not grant entitlement. | Prompt 31/72, Prompt 72/72 |
| LNURLPAY-10 | Lightning Address treated as identity | `name@domain` becomes account identity. | Privacy/auth confusion. | Medium | High | Lightning Address records | Payment UX only; no identity semantics; principal from proof, not address. | Lightning Address cannot authorize. | Prompt 37/72, Prompt 38/72, Prompt 72/72 |

## 9. LNURL-withdraw Threats

| ID | Threat | Scenario | Impact | Likelihood | Severity | Affected Assets | Mitigation | Required Tests | Implementation Prompts |
| -- | ------ | -------- | ------ | ---------- | -------- | --------------- | ---------- | -------------- | ---------------------- |
| WITHDRAW-01 | Withdraw k1 theft | Attacker gets withdraw QR/k1 and claims payout. | Funds loss. | Medium | Critical | Withdraw k1/request | Auth before QR for valuable payouts; policy before request; short TTL; limits; audit. | Valuable withdraw QR requires auth/policy; stolen k1 limited. | Prompt 44/72, Prompt 46/72, Prompt 72/72 |
| WITHDRAW-02 | Withdraw issued without policy | Refund QR generated before entitlement/role/refund checks. | Unauthorized payout. | Medium | Critical | Withdraw request, Policy Decision | Policy Engine before QR; refund state machine; risk checks. | QR not generated before policy approval. | Prompt 44/72, Prompt 46/72 |
| WITHDRAW-03 | Excessive payout | Wallet submits invoice above allowed amount. | Overpayment. | Medium | High | Withdraw callback | Min/max withdrawable; amount policy; business limits; manual review threshold. | Oversized invoice rejected. | Prompt 45/72, Prompt 48/72 |
| WITHDRAW-04 | Replayed withdraw invoice | Same k1/payment request used multiple times. | Duplicate payout. | Medium | Critical | Withdraw k1 | Single-use k1; withdraw status machine; idempotent payment execution. | Duplicate k1/invoice idempotent. | Prompt 45/72, Prompt 48/72 |
| WITHDRAW-05 | PayRegister refund abuse | Cashier issues unauthorized refund. | Merchant funds loss. | Medium | Critical | PayRegister context, Business role | Cashier limits; owner/admin step-up; shift policy; audit packet. | Cashier refund over limit denied. | Prompt 47/72, Prompt 52/72, Prompt 72/72 |
| WITHDRAW-06 | Faucet abuse | Testnet/signet faucet drained. | Resource exhaustion. | High | Medium | Withdraw request | Rate limits, principal/device limits, captcha if allowed, policy throttling. | Faucet per-principal/device limit enforced. | Prompt 44/72, Prompt 48/72 |

## 10. Lightning Address Threats

| ID | Threat | Scenario | Impact | Likelihood | Severity | Affected Assets | Mitigation | Required Tests | Implementation Prompts |
| -- | ------ | -------- | ------ | ---------- | -------- | --------------- | ---------- | -------------- | ---------------------- |
| LNADDR-01 | Lightning Address confused with identity | Address is treated as account identity. | Auth/privacy failure. | Medium | High | Lightning Address, Principal | Payment routing UX only; no identity semantics. | Address cannot authorize access. | Prompt 37/72, Prompt 72/72 |
| LNADDR-02 | Merchant custom domain hijack | Attacker controls merchant domain records. | Payment diversion. | Medium | Critical | Merchant Lightning Address | Domain verification, ownership/admin policy, audit. | Custom domain requires verification. | Prompt 42/72, Prompt 72/72 |
| LNADDR-03 | Wrong product address maps wrong plan | `lite@` returns Pro metadata or vice versa. | Under/over payment, wrong entitlement. | Medium | High | Product registry, payment request | Product registry with status; canonical plan mapping. | Product address maps expected plan only. | Prompt 39/72, Prompt 28/72 |
| LNADDR-04 | Stale static QR resolves retired product | Old QR still accepts purchases. | Unsupported entitlement/sales issue. | Medium | Medium | Lightning Address records | Product status, expiry/deprecation metadata, audit resolution. | Retired product address disabled/redirected safely. | Prompt 37/72, Prompt 39/72 |
| LNADDR-05 | Address enumeration reveals merchants | Public well-known endpoint lists or confirms private merchants. | Privacy leak. | Medium | Medium | Lightning Address records | Minimal metadata, public/private metadata separation. | Unknown/private names return safe response. | Prompt 37/72, Prompt 38/72 |
| LNADDR-06 | Well-known leaks internal metadata | Endpoint returns merchant/customer internals. | Privacy/business leak. | Medium | High | Lightning Address records | Minimal LNURL-pay-compatible metadata only. | No internal metadata in well-known response. | Prompt 38/72, Prompt 72/72 |

## 11. PayRegister LNURL Threats

| ID | Threat | Scenario | Impact | Likelihood | Severity | Affected Assets | Mitigation | Required Tests | Implementation Prompts |
| -- | ------ | -------- | ------ | ---------- | -------- | --------------- | ---------- | -------------- | ---------------------- |
| PAYREG-01 | Static QR reused for wrong store | QR from one store used at another. | Misrouted payments. | Medium | High | PayRegister terminal context | `terminal_id` hash, store binding, signed receipt packet. | QR store binding validated. | Prompt 40/72, Prompt 43/72 |
| PAYREG-02 | Cashier metadata tampered | Cashier/shift fields modified. | Fraud/accounting errors. | Medium | High | Cashier shift metadata | Shift binding, canonical metadata hash, audit. | Tampered shift metadata rejected. | Prompt 41/72, Prompt 54/72 |
| PAYREG-03 | Terminal context spoofed | Fake terminal submits payments/refunds. | Fraud/refund abuse. | Medium | Critical | Terminal context | Terminal hash, device binding, revocation target. | Unknown/revoked terminal denied. | Prompt 40/72, Prompt 53/72 |
| PAYREG-04 | Offline mode accepts stale policy | Local mode ignores revocation/policy epoch. | Unauthorized offline actions. | Medium | High | Offline pack, revocation epoch | Revocation epoch, expiry, policy checkpoint. | Stale offline pack rejected. | Prompt 61/72, Prompt 63/72 |
| PAYREG-05 | Receipt metadata leaks customer data | Receipt includes email/name/payment identifiers. | Privacy leak. | Medium | High | Receipt metadata, payerData | Minimal receipt metadata, redaction, retention. | Receipt contains no raw personal/payment secrets. | Prompt 43/72, Prompt 54/72 |
| PAYREG-06 | Refund bypasses owner policy | Refund path skips owner/admin step-up. | Funds loss. | Medium | Critical | Refund request, Business role | Owner/admin step-up for refunds; shift/role limits. | Refund requires policy/step-up. | Prompt 47/72, Prompt 52/72 |
| PAYREG-07 | Merchant domain misconfiguration | Wrong Lightning Address domain routes funds incorrectly. | Payment loss/customer confusion. | Medium | High | Merchant Lightning Address | Merchant domain policy, verification, audit. | Domain config validation tests. | Prompt 42/72, Prompt 72/72 |

## 12. Recovery Threats

| ID | Threat | Scenario | Impact | Likelihood | Severity | Affected Assets | Mitigation | Required Tests | Implementation Prompts |
| -- | ------ | -------- | ------ | ---------- | -------- | --------------- | ---------- | -------------- | ---------------------- |
| RECOVERY-01 | LNURL-auth alone completes high-value recovery | Fresh LNURL-auth proof resets Pro/Business/Enterprise. | Account takeover. | Medium | Critical | Recovery Capsule, Lightning Principal | LNURL-auth one factor only; profile-specific multi-factor quorum. | LNURL-auth alone denied for high-value recovery. | Prompt 57/72, Prompt 58/72, Prompt 72/72 |
| RECOVERY-02 | Support-only recovery appears | Support manually resets access. | Insider/social takeover. | Medium | Critical | Recovery Capsule | No support-only recovery; policy/audit/quorum. | No support reset endpoint/path. | Prompt 57/72, Prompt 72/72 |
| RECOVERY-03 | Email-only recovery reintroduced | Email link recovers wallet principal. | Account takeover/privacy regression. | Medium | High | Recovery service | Email not sufficient; no mandatory email. | Email-only factor denied. | Prompt 57/72, Prompt 72/72 |
| RECOVERY-04 | Invoice-only recovery reintroduced | Payment proof alone recovers access. | Purchaser takeover. | Medium | High | Payment proof, Recovery | Invoice/payment one possible factor only; not sufficient. | Invoice-only recovery denied. | Prompt 57/72, Prompt 58/72 |
| RECOVERY-05 | Bitcoin seed/private key requested | Recovery asks for seed/private key. | Catastrophic custody breach. | Low | Critical | Wallet, Recovery | No seed/private-key inputs; sensitive input rejection. | Seed/private key rejected everywhere. | Prompt 57/72, Prompt 70/72, Prompt 72/72 |
| RECOVERY-06 | Recovery capsule leaked | Capsule content exposed. | Recovery compromise. | Medium | Critical | Recovery Capsule | Encryption, access policy, redaction, audit. | Capsule not logged/exported raw. | Prompt 57/72, Prompt 54/72 |
| RECOVERY-07 | Recovery cooldown bypassed | Repeated attempts brute-force factors. | Account takeover. | Medium | High | Recovery service | Cooldown, rate limits, audit. | Cooldown enforced per principal/device. | Prompt 57/72 |
| RECOVERY-08 | Business quorum bypassed | Business/Enterprise recovered with single factor. | Enterprise takeover. | Medium | Critical | Multi-wallet quorum | Multi-wallet/multi-method quorum. | Business quorum required. | Prompt 59/72, Prompt 72/72 |
| RECOVERY-09 | Duplicate wallet proof counted twice | Same wallet contributes multiple quorum factors. | Quorum bypass. | Medium | High | Multi-wallet quorum | Unique principal/proof method accounting. | Duplicate principal counted once. | Prompt 59/72 |
| RECOVERY-10 | Recovery audit missing | Recovery starts/completes without audit events. | No forensic trail. | Medium | High | Audit Chain | Mandatory recovery audit events. | Recovery events emitted for success/failure. | Prompt 54/72, Prompt 57/72 |

## 13. Policy Engine Threats

| ID | Threat | Scenario | Impact | Likelihood | Severity | Affected Assets | Mitigation | Required Tests | Implementation Prompts |
| -- | ------ | -------- | ------ | ---------- | -------- | --------------- | ---------- | -------------- | ---------------------- |
| POLICY-01 | Endpoint checks only session | Protected endpoint validates session but skips policy. | Authorization bypass. | Medium | Critical | Policy Decision, PoP Session | `require_policy_decision` dependency and release gates. | Protected endpoint requires policy. | Prompt 51/72, Prompt 66/72, Prompt 72/72 |
| POLICY-02 | LNURL-auth bypasses subscription | LNURL-auth session accesses paid API without entitlement. | Revenue/access loss. | Medium | Critical | Entitlement, Policy | Subscription check in policy for LNURL actors. | LNURL-auth alone denied premium API. | Prompt 49/72, Prompt 51/72 |
| POLICY-03 | LNURL-pay bypasses entitlement rules | Payment path creates entitlement outside policy constraints. | Wrong access/scopes. | Medium | High | Entitlement, Policy | Payment proof binding validated by entitlement and policy. | Entitlement scopes validated after payment. | Prompt 33/72, Prompt 49/72, Prompt 51/72 |
| POLICY-04 | Legacy signature bypasses high-risk policy | Low-strength proof accepted for critical action. | Privilege escalation. | Medium | Critical | Wallet Proof, Policy | `auth_method` and proof strength enforced. | Legacy denied for high-risk. | Prompt 12/72, Prompt 51/72 |
| POLICY-05 | PayRegister role bypass | Cashier performs admin/owner action. | Funds/business compromise. | Medium | Critical | Business role, PayRegister | PayRegister role context, owner/admin step-up. | Cashier denied owner actions. | Prompt 50/72, Prompt 51/72, Prompt 52/72 |
| POLICY-06 | Stale policy hash accepted | Signed old intent with stale policy hash used later. | Policy downgrade. | Medium | High | Structured Intent, Policy | Policy hash in intent, freshness, invalidation. | Stale policy hash rejected. | Prompt 8/72, Prompt 51/72 |
| POLICY-07 | Object-level authorization missing | Principal accesses another business/store/refund. | Cross-tenant access. | Medium | Critical | Policy Decision, Business role | Object-level authorization mandatory. | Cross-tenant object denied. | Prompt 51/72, Prompt 72/72 |
| POLICY-08 | Metric entitlement bypass | Metric endpoint checks plan but not metric group/quota. | Paid data leakage. | Medium | High | Metric Entitlement | Metric entitlement and quota checks. | Metric group/quota enforced. | Prompt 49/72, Prompt 51/72 |

## 14. Audit Threats

| ID | Threat | Scenario | Impact | Likelihood | Severity | Affected Assets | Mitigation | Required Tests | Implementation Prompts |
| -- | ------ | -------- | ------ | ---------- | -------- | --------------- | ---------- | -------------- | ---------------------- |
| AUDIT-01 | Raw address logged | Logs/audit store public address. | Privacy leak. | Medium | High | address_hash, Audit | Redaction; hash/fingerprint only. | No raw address in audit/logs. | Prompt 54/72, Prompt 72/72 |
| AUDIT-02 | Raw k1 logged | k1 appears in logs. | Replay/auth risk. | Medium | Critical | LNURL k1 | Hash k1; redact raw k1. | No raw k1 in logs/audit. | Prompt 21/72, Prompt 54/72 |
| AUDIT-03 | Raw signature logged | Wallet/LNURL signature stored raw. | Privacy/replay risk. | Medium | High | Wallet proof, LNURL callback | Signature hash/fingerprint only. | Raw signature absent. | Prompt 54/72 |
| AUDIT-04 | Raw session token logged | Session token appears in logs. | Session takeover. | Medium | Critical | Session token | Redaction, token hash only. | No raw session in logs/audit. | Prompt 18/72, Prompt 54/72 |
| AUDIT-05 | Missing failed auth audit | Failed wallet/LNURL attempts unrecorded. | No detection. | Medium | High | Audit Chain | Mandatory success/failure events. | Failed auth audited. | Prompt 27/72, Prompt 54/72 |
| AUDIT-06 | Audit chain tampering | Audit event rewritten/deleted undetected. | Evidence loss. | Low | Critical | Audit Chain | Hash chain, transparency checkpoints. | Tamper verification fails. | Prompt 54/72, Prompt 63/72 |
| AUDIT-07 | Payment proof not linked | LNURL payment proof lacks audit event linkage. | Weak payment evidence. | Medium | High | Payment proof, Audit | Payment proof creation audit link. | Payment proof has audit event hash. | Prompt 32/72, Prompt 54/72 |
| AUDIT-08 | Withdraw lacks audit packet | Payout/refund executed without packet. | No forensic trail. | Medium | Critical | Withdraw request, Audit | Mandatory withdraw audit packet. | Withdraw emits audit packet. | Prompt 48/72, Prompt 54/72 |

## 15. Revocation Threats

| ID | Threat | Scenario | Impact | Likelihood | Severity | Affected Assets | Mitigation | Required Tests | Implementation Prompts |
| -- | ------ | -------- | ------ | ---------- | -------- | --------------- | ---------- | -------------- | ---------------------- |
| REVOCATION-01 | Revoked Lightning Principal can login | LNURL-auth ignores principal revocation. | Account compromise persists. | Medium | Critical | Lightning Principal | Revocation Registry target check. | Revoked LNURL principal denied. | Prompt 53/72, Prompt 66/72 |
| REVOCATION-02 | Revoked k1 accepted | Revoked auth/withdraw k1 still works. | Replay/payout abuse. | Medium | Critical | LNURL k1 | k1 revocation target and registry check. | Revoked k1 rejected. | Prompt 21/72, Prompt 53/72 |
| REVOCATION-03 | Revoked device creates session | Device revocation not checked at session creation. | Persistent compromise. | Medium | Critical | Device Binding | Device revocation on session create/use. | Revoked device cannot create/use session. | Prompt 16/72, Prompt 53/72 |
| REVOCATION-04 | Revoked entitlement works | Entitlement revoked but still authorizes. | Unauthorized paid access. | Medium | Critical | Entitlement | Entitlement revocation state in policy. | Revoked entitlement denied. | Prompt 49/72, Prompt 53/72 |
| REVOCATION-05 | Revoked terminal accepts payments/refunds | PayRegister terminal revocation ignored. | Merchant fraud. | Medium | High | PayRegister terminal | Terminal revocation target and policy check. | Revoked terminal denied. | Prompt 40/72, Prompt 53/72 |
| REVOCATION-06 | Offline pack ignores revocation epoch | Offline access remains valid after revocation. | Stale offline trust. | Medium | High | Offline Validity Pack | Revocation epoch embedded/checked. | Stale epoch rejected. | Prompt 61/72, Prompt 53/72 |
| REVOCATION-07 | Principal lockdown does not freeze sessions | Lockdown revokes principal but sessions continue. | Continued access after incident. | Medium | Critical | Principal, Sessions | Session freeze on principal lockdown. | Lockdown freezes active sessions. | Prompt 53/72, Prompt 66/72 |

## 16. Privacy Threats

| ID | Threat | Scenario | Impact | Likelihood | Severity | Affected Assets | Mitigation | Required Tests | Implementation Prompts |
| -- | ------ | -------- | ------ | ---------- | -------- | --------------- | ---------- | -------------- | ---------------------- |
| PRIVACY-01 | Wallet address global tracking id | Raw/hash reused globally. | Cross-product tracking. | High | High | address_hash | HMAC lookup, per-product pseudonyms. | No raw/global id. | Prompt 7/72, Prompt 15/72 |
| PRIVACY-02 | LNURL key hash links products | Same hash reused for all product contexts. | Cross-product tracking. | High | High | lnurl_key_hash | Product-scoped aliases, separate LNURL Auth DB. | Different aliases per product. | Prompt 7/72, Prompt 24/72 |
| PRIVACY-03 | payerData creates personal profile | Email/name/identifier stored broadly. | Privacy/compliance risk. | Medium | High | payerData | Minimal payerData, no mandatory email, retention. | Email/name optional off by default. | Prompt 36/72 |
| PRIVACY-04 | Payment DB linked to Usage DB | Direct joins deanonymize usage. | Behavioral profiling. | Medium | High | Payment/Usage DB | DB separation, pseudonymous joins only by policy. | No direct raw identifier joins. | Prompt 7/72, Prompt 56/72 |
| PRIVACY-05 | Lightning Address reveals info | Address metadata exposes products/merchants/customers. | Privacy/business leak. | Medium | Medium | Lightning Address | Minimal metadata, public/private separation. | Well-known response minimal. | Prompt 37/72, Prompt 38/72 |
| PRIVACY-06 | Receipt leaks customer metadata | PayRegister receipt includes PII/payment secrets. | Customer privacy leak. | Medium | High | Receipt metadata | Receipt minimization, redaction. | Receipt has no PII by default. | Prompt 43/72 |
| PRIVACY-07 | Audit logs deanonymize principals | Audit events include raw identifiers. | Privacy breach. | Medium | High | Audit Chain | Hash/fingerprint only, redaction. | Audit redaction tests. | Prompt 54/72 |
| PRIVACY-08 | Dedicated auth warning missing | Users use treasury/cold wallet routinely. | Privacy/treasury risk. | Medium | High | Wallet Principal | Dedicated auth address and cold treasury warnings. | UI/SDK docs contain warnings. | Prompt 70/72, Prompt 71/72 |

## 17. PQ / Crypto-Agility Threats

| ID | Threat | Scenario | Impact | Likelihood | Severity | Affected Assets | Mitigation | Required Tests | Implementation Prompts |
| -- | ------ | -------- | ------ | ---------- | -------- | --------------- | ---------- | -------------- | ---------------------- |
| PQ-01 | Fake PQ implementation claim | Docs/API claim PQ algorithms implemented without code. | False assurance. | Medium | High | PQ issuer chain | Truthful docs; unsupported PQ fails safely. | No fake PQ claims. | Prompt 62/72, Prompt 72/72 |
| PQ-02 | Classical-only issuer treated 20-year-safe | Long-term artifact marketed as PQ-secure. | Future integrity risk. | Medium | High | Offline pack, Certificate | Signature suite metadata and risk labels. | Classical suite not labeled PQ. | Prompt 62/72 |
| PQ-03 | crypto_epoch missing | Issued objects cannot support rotation. | Migration/rotation failure. | Medium | High | Entitlement, Certificate | `crypto_epoch` on Bastion-issued objects. | crypto_epoch required. | Prompt 62/72 |
| PQ-04 | PQ metadata inconsistent | Objects disagree on suite/epoch. | Verification failure. | Medium | Medium | Issued objects | Canonical suite metadata. | Metadata consistency tests. | Prompt 62/72 |
| PQ-05 | Wallet proof confused with PQ protection | Bitcoin/LNURL signatures described as PQ-secure. | False assurance. | Medium | High | Wallet Proof | State wallet proofs remain classical unless ecosystem changes. | Docs/API label classical wallet proofs. | Prompt 62/72, Prompt 72/72 |
| PQ-06 | Issuer key rotation not audited | Rotation occurs without evidence. | Undetected key misuse. | Medium | High | Issuer keys, Audit | Issuer key rotation audit, transparency checkpoint. | Rotation emits audit/checkpoint. | Prompt 54/72, Prompt 63/72 |

## 18. Risk Matrix

| Risk | Severity | Likelihood | Owner/component | First implementation prompt mitigating it | Release gate required |
|---|---:|---:|---|---|---:|
| Wallet proof treated as full authorization | Critical | Medium | Wallet Auth / Policy | Prompt 18/72 | Yes |
| LNURL-auth k1 replay | Critical | High | LNURL Auth | Prompt 21/72 | Yes |
| LNURL-pay invoice issued treated as settled | Critical | High | LNURL Pay / Entitlements | Prompt 31/72 | Yes |
| LNURL-withdraw k1 theft | Critical | Medium | LNURL Withdraw / Risk | Prompt 44/72 | Yes |
| Bitcoin seed/private key accepted | Critical | Low | Wallet Auth / Recovery / UI | Prompt 57/72 | Yes |
| Policy Engine bypass | Critical | Medium | API / Policy | Prompt 51/72 | Yes |
| Raw secrets in logs | Critical | Medium | Audit / Logging | Prompt 54/72 | Yes |
| Lightning Address treated as identity | High | Medium | Lightning Address / Policy | Prompt 37/72 | Yes |
| payerData privacy leak | High | Medium | LNURL Pay / Privacy | Prompt 36/72 | Yes |
| Access Certificate becomes bearer access | Critical | Medium | Access Certificate / Dependencies | Prompt 60/72 | Yes |
| Support-only recovery | Critical | Medium | Recovery | Prompt 57/72 | Yes |
| PayRegister refund abuse | Critical | Medium | PayRegister / Withdraw | Prompt 47/72 | Yes |

## 19. Test Plan

| Future test file | Purpose | Major assertions | Related threats |
|---|---|---|---|
| `tests/security/test_wallet_signature_not_full_access.py` | Prove wallet proof is not authorization. | Wallet signature alone denied; policy invoked. | WALLET-01, POLICY-01 |
| `tests/security/test_wallet_address_not_user_id.py` | Prevent raw/global address identity. | No raw address as user_id/schema/log. | WALLET-03, PRIVACY-01 |
| `tests/security/test_wallet_no_seed_private_key.py` | Enforce no custody inputs. | Seed/private key/mnemonic rejected everywhere. | RECOVERY-05 |
| `tests/security/test_wallet_replay_protection.py` | Validate wallet/PoP nonce protections. | Duplicate nonce rejected; timestamp skew enforced. | WALLET-09 |
| `tests/security/test_wallet_legacy_signature_limits.py` | Limit fallback signature strength. | Legacy signature denied high-risk actions. | WALLET-06, POLICY-04 |
| `tests/security/test_wallet_step_up_required.py` | Require step-up for sensitive actions. | Device add/recovery/admin actions need fresh proof. | WALLET-08, LNURLAUTH-10 |
| `tests/security/test_wallet_sensitive_redaction.py` | Prevent raw wallet/session material leaks. | No raw address/signature/session in logs/audit. | AUDIT-01..04, PRIVACY-07 |
| `tests/security/test_lnurl_k1_replay.py` | Validate k1 lifecycle. | Reused/unknown/expired k1 rejected. | LNURLAUTH-01..03, REVOCATION-02 |
| `tests/security/test_lnurl_auth_not_full_access.py` | Prove LNURL-auth is not authorization. | LNURL-auth alone denied protected access. | LNURLAUTH-06, POLICY-02 |
| `tests/security/test_lnurl_pay_requires_settlement.py` | Gate entitlements on settlement. | Invoice creation/pending verify grants no entitlement. | LNURLPAY-01, LNURLPAY-09 |
| `tests/security/test_lnurl_withdraw_policy_required.py` | Gate valuable withdraw QR. | QR not issued before auth/policy; amount limits. | WITHDRAW-01..04 |
| `tests/security/test_lnurl_payerdata_privacy.py` | Keep payerData minimal. | Email/name not mandatory; minimal retention. | LNURLPAY-06..07, PRIVACY-03 |
| `tests/security/test_lightning_address_not_identity.py` | Keep Lightning Address payment-only. | Address cannot authorize or become user_id. | LNADDR-01, LNURLPAY-10 |
| `tests/security/test_payregister_lnurl_refund_policy.py` | Prevent refund abuse. | Cashier limits; owner/admin step-up; terminal binding. | PAYREG-03, PAYREG-06, WITHDRAW-05 |
| `tests/integration/test_wallet_lnurl_full_flow.py` | End-to-end happy and denied flows. | Wallet/LNURL auth + device + PoP + policy + entitlement. | WALLET-01, LNURLAUTH-01, LNURLPAY-01 |
| `tests/contract/test_lnurl_openapi_contract.py` | Contract safety for future routes. | No seed/private key fields; callbacks documented; safe schemas. | POLICY-01, PQ-01 |

## 20. Implementation Mapping

| Prompt | Threat areas addressed |
|---|---|
| Prompt 3/72 — Wallet + LNURL auth domain package | Principal boundaries, domain concepts, WALLET-03, LNURLAUTH-05 |
| Prompt 4/72 — Wallet + LNURL schemas | Safe schemas, no seed/private key fields, API contracts |
| Prompt 5/72 — Wallet + LNURL DB models | HMAC identifiers, no raw k1/session/address columns |
| Prompt 7/72 — Wallet privacy commitments | WALLET-03, WALLET-10, PRIVACY-01..08 |
| Prompt 8/72 — Structured Bastion Auth Intent | WALLET-02, POLICY-06 |
| Prompt 18/72 — Wallet PoP request verifier | WALLET-01, WALLET-09 |
| Prompt 21/72 — LNURL k1 registry and replay protection | LNURLAUTH-01..05, REVOCATION-02 |
| Prompt 22/72 — LNURL-auth challenge service | LNURL action/domain binding |
| Prompt 23/72 — LNURL-auth callback verifier | Callback signature/k1 verification |
| Prompt 31/72 — LNURL-verify settlement service | LNURLPAY-01, LNURLPAY-09 |
| Prompt 36/72 — LNURL payerData.auth binding | LNURLPAY-06..07, PRIVACY-03 |
| Prompt 44/72 — LNURL-withdraw request service | WITHDRAW-01..02, WITHDRAW-06 |
| Prompt 49/72 — Wallet-bound Subscription Entitlements | POLICY-02..03, REVOCATION-04 |
| Prompt 51/72 — LNURL Policy Engine hooks | POLICY-01..08, WALLET-01 |
| Prompt 53/72 — Wallet + LNURL Revocation extensions | REVOCATION-01..07 |
| Prompt 54/72 — Wallet + LNURL Audit Chain events | AUDIT-01..08, recovery/payment audit |
| Prompt 57/72 — Recovery Capsule foundation | RECOVERY-01..10 |
| Prompt 58/72 — LNURL-auth as recovery factor | RECOVERY-01, RECOVERY-04 |
| Prompt 63/72 — Transparency checkpoints for wallet/LNURL auth | AUDIT-06, PQ-06 |
| Prompt 72/72 — Final Wallet-first + LNURL production release gate | All invariants and critical/high risks |

## 21. Release Gate Requirements

By Prompt 72/72, the release gate must fail if:

- wallet signature alone grants protected access;
- LNURL-auth alone grants protected access;
- reused `k1` is accepted;
- unexpected `k1` is accepted;
- expired `k1` is accepted;
- invoice issued creates entitlement without settlement;
- LNURL-withdraw QR is created before policy approval for valuable payout;
- Lightning Address becomes identity;
- `payerData.email` is mandatory;
- `commentAllowed` grants authorization;
- `successAction` leaks raw secret;
- Bitcoin seed/private key is accepted;
- legacy signature approves high-risk action;
- protected endpoint bypasses Policy Engine;
- raw address/k1/signature/session token appears in logs;
- revoked principal/device/session/proof still works;
- Access Certificate works as bearer access;
- docs claim fake PQ implementation.

## 22. Acceptance Criteria

- [x] `docs/WALLET_FIRST_LNURL_THREAT_MODEL.md` exists.
- [x] All required asset categories are covered.
- [x] All required trust boundaries are covered.
- [x] All hard invariants are listed.
- [x] All wallet-first threats are covered.
- [x] All LNURL-auth threats are covered.
- [x] All LNURL-pay threats are covered.
- [x] All Lightning Address threats are covered.
- [x] All LNURL-withdraw threats are covered.
- [x] PayRegister LNURL threats are covered.
- [x] Recovery threats are covered.
- [x] Policy threats are covered.
- [x] Audit threats are covered.
- [x] Revocation threats are covered.
- [x] Privacy threats are covered.
- [x] PQ/crypto-agility threats are covered.
- [x] Risk matrix exists.
- [x] Test plan exists.
- [x] Threat-to-prompt mapping exists.
- [x] Release-gate requirements exist.
- [x] No runtime code changed.
- [x] No DB models added.
- [x] No migrations added.
- [x] No fake implementation claims added.
