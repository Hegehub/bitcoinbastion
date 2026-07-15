# Wallet-first + LNURL Migration Audit

Prompt: **0/72 — Wallet-first + LNURL Migration Audit**. Scope: audit-only; no runtime behavior, migrations, routes, SDKs, frontend, or tests were changed.

## 1. Executive Summary

The repository already contains the Bastion Proof-of-Access Auth system centered on access payment intents, Access Certificates, subscription entitlements, device keys, challenges, short-lived sessions, request-signature proof-of-possession, policy checks, revocation, audit-chain events, recovery/quorum, child API keys, delegated passes, BTCPay/manual payment providers, SDK support, UI safety copy, and release-gate tests. The active protected access dependency rejects `Authorization: Bearer` and builds `AccessContext` from Bastion `X-Bastion-*` session/signature headers. Legacy `/auth/register` and `/auth/login` remain as disabled `410 Gone` stubs.

Wallet-first is being added so a wallet-controlled principal can become the primary actor for access flows without making Bastion wallet-only. LNURL is being added so Lightning wallets can participate natively in proof, payment, activation, withdraw/refund, and Lightning Address UX while still passing through Bastion PoP, Policy, Audit, and Revocation.

Target primary actors:

- **Wallet Principal becomes the primary actor for wallet-first flows.**
- **Lightning Principal becomes the primary actor for LNURL-auth flows.**
- **Access Certificate remains an optional high-assurance bridge**, not the only actor.
- **`bastion-pass.bbp` remains an optional high-assurance/export/offline artifact.**
- **LNURL Layer is an adapter layer**, not a replacement for PoP Session, Policy Engine, Audit Chain, Revocation Registry, device continuity, or entitlement checks.

Core audit finding: no password/bearer/JWT path was found that can grant protected Access Layer access. Legacy auth schemas/security helpers remain as fail-closed compatibility residue and deployment config still contains `JWT_SECRET_KEY`/bot bearer references that require future cleanup or explicit classification.

## 2. Current Access Layer Surface Map

Classification legend: **compatible** = can remain and be extended safely; **requires extension** = must gain wallet/LNURL fields or hooks; **requires replacement** = likely must be redesigned; **legacy auth risk** = safe only if kept disabled or removed; **manual review** = not enough signal for final production claims.

| Surface | Relevant files/modules inspected | Classification | Notes |
|---|---|---:|---|
| Access domain | `app/domain/access/context.py`, `decisions.py`, `entitlements.py`, `errors.py`, `metrics.py`, `plans.py`, `scopes.py` | requires extension | Strong hash/fingerprint-first `AccessContext`, but currently certificate/pass/session-centric; add principal hierarchy and auth/payment methods. |
| Access schemas | `app/schemas/access.py`, `access_intent.py`, `auth.py`, `wallet.py` | requires extension | Access schemas are certificate/payment/session-oriented. `auth.py` is disabled legacy residue. No LNURL/BIP-322 schemas. |
| Access DB models | `app/db/models/access.py`, migration `20260701_0063_access_layer_tables.py`, `20260705_0064_access_human_intents.py` | requires extension | Existing access tables can be bridged; new wallet/LNURL tables required. |
| Access services | `app/services/access/*`, `crypto/*`, `payments/*` | requires extension | Good service boundaries: issuer, session, challenge, request verifier, policy, revocation, audit, payments, recovery. Need wallet proof, BIP-322, LNURL k1 registry, LNURL pay/verify/withdraw. |
| Access API | `app/api/v1/access.py`, `app/api/access_dependencies.py` | requires extension | Existing router is PoA lifecycle; dependencies reject bearer and enforce PoP/policy. New wallet/LNURL routers/dependencies should not overload current paths dangerously. |
| Legacy auth API | `app/api/v1/auth.py`, `app/api/dependencies.py`, `app/core/security.py` | legacy auth risk | Login/register disabled; `get_current_user` and security helpers remain compatibility/test residue. Must not be used for protected Access Layer. |
| API routers | `app/api/v1/*` | mixed | Many premium endpoints already use `require_scope`, `require_plan`, `require_metric_entitlement`, or human intent; public endpoints unaffected. Manual review needed for all new wallet/LNURL protected endpoints. |
| Bot | `app/bot/handlers/access.py`, `commands.py`, `runner.py` | requires extension | Bot has access flow/commands; future bot wallet/LNURL QR flows must use scoped delegated/child pass and policy. |
| Python SDK | `sdk/python/bitcoin_bastion_sdk/access_auth.py`, `auth.py`, `resources/access.py`, `signing.py`, tests | requires extension | Supports PoA headers and rejects legacy bearer-by-default; needs wallet/LNURL helpers. |
| TypeScript SDK | `sdk/typescript/src/auth.ts`, `http.ts`, `resources/access.ts`, examples/tests | requires extension | Legacy bearer config is fail-closed compatibility; needs wallet/LNURL helpers and stricter docs/examples. |
| Historical frontend | removed `frontend/` tree; see archived removal/migration reports | archived | Next.js is not present in the current checkout and is not an active wallet/LNURL surface. |
| Reflex frontend | `reflex_frontend/bastion_ui/*`, docs/tests | requires extension | Sole repository-native UI; Console/Trace/Market and safety checks exist, but wallet-auth/LNURL pages and copy are not wired. |
| CLI | `app/cli/*` if present; no top-level `cli/` found in this checkout | manual review | Future wallet/LNURL CLI may belong under `app/cli`. |
| Tests | `tests/security/*`, `tests/contract/*`, `tests/integration/*`, SDK tests | requires extension | Strong release gates for no bearer/password/seed; add wallet/LNURL replay, settlement, withdraw, privacy gates. |
| Docs | `docs/ADR_BASTION_PROOF_OF_ACCESS_AUTH.md`, `ACCESS_LAYER_RELEASE_GATE.md`, `ACCESS_AUTH_MIGRATION_AUDIT.md`, SDK/frontend docs | compatible + requires extension | Existing PoA docs explicitly anticipate wallet-bound access and LNURL-pay as future work. |
| Environment | `.env.example`, `app/core/config.py`, `docs/ACCESS_ENVIRONMENT.md`, deploy templates | requires extension + legacy auth risk | Add wallet/LNURL env vars; remove or isolate legacy JWT and bearer config. |
| Deploy/Helm/CI | `deploy/kubernetes/base/*`, `helm/bitcoin-bastion/values.yaml`, `.github/workflows/*` | requires extension | Kubernetes secrets include JWT/bot bearer; Helm is values-only with no templates; CI has access gates and needs LNURL release gates. |

## 3. Legacy Auth Residue Audit

Search terms covered: password, username, email, bearer/Bearer, JWT/jwt, access_token, Authorization, LoginRequest, RegisterRequest, TokenResponse, UserRepository, AuthService, get_current_user/current_user, user_id, authenticate, verify_password/hash_password, passlib, jose, SECRET_KEY/JWT_SECRET_KEY, login/register/reset/2FA.

| Occurrence class | Files | Classification | Finding |
|---|---|---:|---|
| Disabled auth endpoints | `app/api/v1/auth.py` | disabled legacy stub | `/register` and `/login` return `410 Gone`, are deprecated, and point to Proof-of-Access replacement. |
| Legacy user dependency | `app/api/dependencies.py` | legacy auth risk | `get_current_user` remains and is not the Access Layer dependency; future protected endpoints must not depend on it. |
| Legacy security helpers | `app/core/security.py`, `tests/security/test_legacy_auth_disabled.py` | disabled legacy stub/test fixture | Hash/JWT helpers are expected to fail closed by tests; ensure no active route uses them for protected Access. |
| Pydantic auth schemas | `app/schemas/auth.py` | disabled legacy stub | `LoginRequest`, `RegisterRequest`, `TokenResponse` residue tested to not accept password/issue tokens. |
| Config/deploy JWT | `app/core/config.py`, `.env.example`, `deploy/kubernetes/base/secret.example.yaml`, `external-secret.example.yaml`, docs operations/security | legacy auth risk | `JWT_SECRET_KEY` persists for legacy/app compatibility. It should not be a release blocker only if no protected Access endpoint consumes JWTs. Future cleanup recommended. |
| Bot bearer token | `BOT_API_BEARER_TOKEN` in config/deploy/docs | SDK compatibility/reference/manual review | Bot/API operational secret, not Access Pass auth. Needs explicit separation from wallet/LNURL auth. |
| SDK bearer residue | Python/TypeScript SDK auth/config/tests/readmes | SDK compatibility reference | Kept for rejected compatibility. Tests assert no `Authorization: Bearer` by default and even opt-in TS path no longer sends it. |
| Tests/docs mentions | `tests/security/*`, `docs/ACCESS_LAYER_RELEASE_GATE.md`, `docs/ACCESS_AUTH_MIGRATION_AUDIT.md`, SDK docs | documentation/test fixture | Historical and gate language is acceptable. |
| OpenAPI disabled auth | `tests/contract/test_access_openapi_contract.py`, `app/api/openapi.py` | documentation/contract | Login/register are marked disabled/deprecated; OpenAPI warns bearer is not accepted. |

**Hard requirement result:** No password/bearer/JWT path was identified that can still grant protected Access Layer access. Active Access dependencies reject bearer and require Bastion session/request proof plus policy. Residual JWT/password symbols are compatibility, disabled stubs, deployment residue, docs, or tests; they remain migration risks if reused by future endpoints.

## 4. Existing Proof-of-Access Auth Audit

| Component | Current repository evidence | Missing for wallet-first/LNURL |
|---|---|---|
| Access Certificate | `AccessCertificate` model, certificate issuer service, issue endpoint, SDK import/export docs | Bridge from wallet/LNURL principal to certificate, optional issuance rules, principal fingerprint fields. |
| Subscription Entitlement | `SubscriptionEntitlement` model/service, plan entitlements, metric catalog | Wallet-bound and LNURL-payment-bound ownership references; settlement-gated LNURL issuance. |
| Device Key | `AccessDevice`, device fingerprint in contexts/sessions | Wallet-device binding and LNURL-auth post-auth device binding. |
| PoP Session | `AccessSession`, session service, request verifier, `X-Bastion-*` headers | Wallet-bound sessions, LNURL-auth session bridge, session nonce table alignment. |
| Policy Engine | `AccessPolicyEngine`, `AccessPolicyContext`, `app/api/access_dependencies.py` | New auth/payment/principal inputs, wallet proof freshness, k1 status, LNURL settlement state. |
| Revocation Registry | `AccessRevocation`, `RevocationRegistry` | New target types for wallet principal, LNURL key/k1, wallet proof/session/device, payment proof, Lightning Address. |
| Audit Chain | `AccessAuditEvent`, `AccessAuditChain` | New wallet/LNURL event types and redaction rules. |
| Recovery | `RecoveryQuorum`, `RecoveryAttempt`, `AccessRecoveryService`, recovery seed/quorum services | Wallet proof factors, LNURL-auth as non-sufficient factor, multi-wallet quorum. |
| Access Integrity | access integrity summary in `/access/me`, release docs/tests | Score 2.0 with LNURL signals, wallet proof freshness, k1 replay status. |
| Payment Proof | `AccessPaymentIntent`, payment intent service, manual/BTCPay providers | LNURL-pay request/invoice/settlement/proof/verify tables and idempotency. |
| Metric Entitlements | `MetricUsage`, metric catalog/costs, plan overlays | Wallet-bound metric entitlement and policy actor metadata. |
| Protected dependencies | `require_access_session`, `require_scope`, `require_plan`, metric/human intent/business role dependencies | Wallet/LNURL auth dependencies with same policy/revocation invariants. |
| Release gates | `tests/security/test_access_layer_release_gate.py`, no password/bearer/seed tests | Add LNURL replay/expiry/settlement/withdraw/successAction/payerData gates. |

## 5. Wallet-first Integration Points

| Integration point | Likely files to modify | New files likely needed | DB impact | Service/API/test impact | Migration risk |
|---|---|---|---|---|---|
| Wallet Principal model | `app/domain/access/context.py`, `app/db/models/access.py`, `app/services/access/policy_context.py` | `app/domain/wallet_auth/*`, `app/db/models/wallet_auth.py` | `wallet_principals`, HMAC lookup IDs | New principal service/API schemas/tests | High: public address must not become global user id. |
| Bitcoin Wallet Principal | `app/schemas/wallet.py`, `app/api/v1/wallet.py`, onchain utilities | BIP-322 verifier interface/service | wallet proof/challenge tables | Challenge, proof verify, registration/login APIs | High: incomplete verifier/fake support. |
| Lightning Wallet Principal | access context/policy/audit | LNURL principal service | `lnurl_principals`, `lnurl_auth_attempts` | LNURL-auth callback/session bridge | High: LNURL-auth over-authorizes. |
| Wallet Proof | crypto/signature services | `wallet_proof_verifier.py`, `bip322.py` | `wallet_proofs`, `wallet_auth_challenges` | Proof freshness/replay tests | High: nonce/domain/action binding. |
| Device Binding | `AccessDevice`, session service | wallet device binding service | `wallet_devices` or extension | bind after proof/LNURL-auth | Medium: device continuity bypass. |
| Wallet-bound Entitlements | entitlement service/model | wallet entitlement binder | extend `subscription_entitlements` | policy actor binding tests | High: entitlement theft/rebinding. |
| Wallet-bound PoP Session | `session_service.py`, request verifier | wallet session bridge | `wallet_sessions`, nonce table | new dependencies/routes | High: wallet proof alone grants access. |
| Wallet-bound Policy | `policy_context.py`, `policy_engine.py`, reasons | principal/auth enums | `policy_decisions` if present/added | new decision reasons/gates | High. |
| Wallet-bound Revocation | `revocation_registry.py`, model enum | revocation extension | extend target enum/metadata | revoke wallet/device/session tests | High. |
| Wallet-bound Audit | `audit_chain.py` | wallet audit event constants | `audit_chain_events`/`access_audit_events` extension | no raw address/signature | Medium. |
| Access Certificate bridge | issuer/session/entitlement services | certificate bridge service | optional principal refs | bridge API/tests | Medium: optional bridge becomes mandatory. |

## 6. BIP-322 / Bitcoin Wallet Proof Audit

Search terms covered: bitcoin, signature, secp256k1, BIP-322, message signing, address validation, descriptor, treasury, wallet health, watch-only, private key, seed, xprv.

Existing reusable pieces:

- Bitcoin-facing advisory surfaces: `app/api/v1/wallet.py`, `app/schemas/wallet.py`, wallet health/domain utilities, Trace/onchain validation docs.
- Signature infrastructure for Access device/session request signing: `app/services/access/crypto/signatures.py`, `request_verifier.py`, SDK signing helpers.
- Strong no-custody safety rules across docs/tests/frontend/SDK/MCP/deploy.
- Treasury modules are draft/review/advisory and explicitly no custody/no private key handling.

Missing BIP-322 infrastructure:

- No production BIP-322 verifier, no BIP-322 challenge schema/service, no address-to-principal privacy commitment, no wallet proof replay/freshness store, no hardware-wallet metadata registry.
- Existing signatures are device/request signing, not Bitcoin ownership proof.

Security rules for future work:

- BIP-322 / Bitcoin message proof must prove Bitcoin ownership/control only; it must not sign transactions or handle custody.
- No seed/private key, WIF, xprv/yprv/zprv, wallet file, descriptor with secrets, or signing material can be requested, stored, logged, or used for auth.
- Treasury/cold-wallet addresses should be discouraged for routine login; UI/SDK must recommend dedicated Bastion auth wallets/addresses.

## 7. LNURL Readiness Audit

Search terms covered: lightning, lnurl, lnurl-auth, lnurl-pay, LNURL, invoice, payment, BTCPay, bolt11, payregister, register, refund, payout, withdraw, lightning address, well-known, lnurlp, payerData, successAction, commentAllowed.

Existing reusable payment/access pieces:

- `app/services/access/payment_intent_service.py` plus `payments/base.py`, `manual.py`, `btcpay.py` provide intent/provider boundaries.
- `AccessPaymentIntent` stores payment method/provider/status and hashed invoice/payment identifiers.
- Access API exposes payment-intent creation/status and certificate issuance after payment settlement/availability checks.
- Metric catalog/policy already includes PayRegister metric/scopes/roles vocabulary.
- BTCPay config exists (`ACCESS_BTCPAY_*`) but no LNURL-native layer was found.

Existing PayRegister surfaces:

- PayRegister appears as metric groups, scopes, business roles, release docs, and Trace platform payment advisory tests/docs.
- No complete PayRegister LNURL-pay/withdraw/receipt/router implementation was found in the audited access layer.

Missing LNURL infrastructure:

- No LNURL encoder/decoder URL safety package, k1 registry, LNURL-auth callback verifier, LNURL-pay callback/invoice service, LNURL-verify settlement endpoint, LNURL-withdraw service, Lightning Address well-known route, `payerData`/`successAction`/`commentAllowed` schemas, or SDK/frontend/CLI helpers.

## 8. LNURL-auth Target Audit

Future system needs: challenge creation, 32 random byte `k1`, k1 hash registry, expiry, single-use enforcement, callback endpoint, signature verifier, compressed secp256k1 public key handling, DER ECDSA signature handling, action mapping (`register`, `login`, `link`, `auth`), Lightning Principal service, device binding after auth, PoP Session issuance after auth, step-up, Policy Engine integration, Audit Chain events, and Revocation Registry targets.

Hard requirements:

- `k1` must be 32 random bytes, expected by the server, single-use, quickly expiring, and removed or marked used.
- Unexpected, reused, expired, wrong-domain, or wrong-action `k1` must be rejected.
- `action=auth` must map to a Bastion policy intent and must not mean broad access.
- LNURL-auth must not grant full access without Device Key, PoP Session, entitlement, revocation check, and Policy Engine allow decision.

Likely files: new `app/services/lnurl/*`, `app/api/v1/lnurl.py`, schemas, models, migrations, policy/audit/revocation extensions, SDK resources, frontend QR pages, security tests.

## 9. LNURL-pay Target Audit

Future system needs: LNURL-pay request service, subscription payment metadata, min/max msat validation, callback endpoint, BOLT-11 issuance, payment proof creation, settlement verification, entitlement issuance, `successAction`, `commentAllowed`, `payerData`, PayRegister metadata, receipt metadata, audit events, and policy hooks.

Hard requirements:

- Invoice generated is not payment settled.
- Subscription entitlement must not be issued until trusted settlement verification says settled.
- `commentAllowed` is untrusted input and must never authorize access.
- `payerData.email` must not be mandatory by default; `payerData.auth` is preferred over personal identity fields.
- `successAction.url` must not leak raw Access Pass, raw session, recovery material, k1, preimage, or secrets.

## 10. Lightning Address Target Audit

Future needs: `GET /.well-known/lnurlp/{name}`, product/subscription/merchant/PayRegister addresses, domain policy, metadata templates, LNURL-pay routing, custom merchant domain support, address ownership/admin policy.

Examples to support as routing UX only: `lite@bitcoin-bastion.com`, `pro@bitcoin-bastion.com`, `business@bitcoin-bastion.com`, `store-123@payregister.bitcoin-bastion.com`, `cashier-01@merchant-domain.com`.

Hard requirement: Lightning Address is payment routing UX and must not be treated as legal identity or authorization identity.

## 11. LNURL-withdraw Target Audit

Future needs: withdraw request creation, withdraw `k1`, callback endpoint, wallet-provided invoice handling, policy approval before valuable QR issuance, refund/payout policy, PayRegister refund integration, audit events, risk limits, cooldowns, revocation.

Use cases: subscription refund, PayRegister refund, cashback, operator reward, bug bounty, partner payout, testnet/signet faucet.

Hard requirements: not an open payout system; valuable withdraw requires auth/policy before QR; valid ephemeral `k1` alone must not bypass business policy; payout must be audited.

## 12. LNURL-verify Target Audit

Future needs: verify endpoint, internal node/BTCPay settlement check, verify URL support, preimage handling if available, invoice status mapping, payment proof creation, entitlement issuance gate.

Hard requirements: no entitlement on invoice creation, no entitlement on pending invoice, trusted `settled=true` or equivalent required, duplicate verification idempotent.

## 13. payerData / successAction / commentAllowed Audit

Future requirements:

- `payerData.auth`, `payerData.pubkey`, `payerData.identifier`, optional `payerData.email`.
- `successAction.message` and safe/short-lived `successAction.url`.
- `commentAllowed` as untrusted UX metadata only.

Privacy/security rules: minimal payerData; email disabled/not mandatory by default; comments never authorize; successAction never exposes raw secrets; `payerData.auth` may bind payment and auth proof but still goes through Policy Engine.

## 14. Principal Model Expansion Audit

Current `AccessContext` is certificate/pass/session/device-centric and no global `user_id` is present in the Access context. Legacy user models/routes exist outside Access. Policy actor modeling uses plan/scope/object/business-role fields rather than a full principal hierarchy.

Target hierarchy: Wallet Principal → Bitcoin Wallet Principal / Lightning Wallet Principal; Device Principal; Access Certificate Principal; Child API Key Principal; Business Role Principal; PayRegister Device Principal; Bot Principal.

Hard requirements: no global `user_id` by default; Bitcoin address is not public user id; LNURL linking key is not public user id; Lightning Address is not identity by itself; use HMAC-SHA256 lookup identifiers with server pepper/domain separation.

## 15. Policy Engine Impact

Existing files: `app/services/access/policy_engine.py`, `policy_context.py`, `policy_reasons.py`, `app/api/access_dependencies.py`.

Required new inputs: `auth_method=wallet_proof|bip322|legacy_bitcoin_message|lnurl_auth`, `payment_method=lnurl_pay`, `withdraw_method=lnurl_withdraw`, `principal_type=bitcoin_wallet_principal|lightning_wallet_principal`, proof strength/freshness, k1 status, device binding, PoP status, subscription/metric entitlement, revocation status, step-up, business role, PayRegister device context, recovery state.

New decision reasons: wallet proof stale/weak, LNURL k1 invalid/replayed/expired, wallet principal revoked, Lightning principal revoked, settlement required, withdraw policy required, step-up required, Lightning Address not identity, payerData insufficient.

High-risk actions require human intent/step-up and audit. Release gates must fail if any new wallet/LNURL path bypasses Policy Engine.

## 16. Audit Chain Impact

Required new event types: wallet challenge/registration/login/device/session/step-up/recovery/lockdown events; LNURL-auth challenge/callback events; LNURL-pay request/invoice/verified/failed/entitlement events; withdraw request/invoice/paid/failed; Lightning Address resolved; payerData received; successAction issued.

Rules: no raw address, raw signature, raw k1 (store hash), raw session/pass/recovery material, preimage, or private key in audit. Use hashes/fingerprints only.

## 17. Revocation Registry Impact

Current model supports target types: pass, certificate, entitlement, device, session, child API key, delegated pass, offline pack, issuer key, recovery quorum, workspace role.

Required targets: bitcoin_wallet_principal, lightning_wallet_principal, wallet_proof, lnurl_auth_key, lnurl_k1, wallet_device, wallet_session, wallet_step_up_proof, wallet_bound_entitlement, lnurl_payment_proof, lnurl_withdraw_request, lightning_address, payregister_device, access_certificate, offline_validity_pack.

Blast-radius scenarios: stolen wallet auth key, domain migration duplicate principals, compromised device, replayed k1, incorrectly issued entitlement, leaked successAction, compromised PayRegister terminal, refund/payout abuse. Tests need revocation per target and cross-target non-overreach.

## 18. Recovery / Quorum Impact

Recovery must support BIP-322 ownership proof, LNURL-auth as a recovery factor, trusted device history, payment proof, recovery file, owner/admin wallet quorum, hardware wallet proof, air-gapped proof, transparency checkpoint.

Rules: LNURL-auth alone cannot complete high-value recovery; wallet signature alone cannot complete Business/Enterprise recovery; no seed/private key input; no support-only reset; recovery audited; recovery not easier than login.

## 19. PayRegister Impact

Current repository signal: PayRegister scopes/metrics/roles exist in policy and metric catalog; docs/tests mention register/payment advisory and business workflows. Full PayRegister LNURL surfaces were not found.

Target flows: static LNURL-pay QR, NFC LNURL payment link, cashier shift metadata, terminal metadata, store Lightning Address, PayRegister refund via LNURL-withdraw, owner proof via LNURL-auth or BIP-322, business policy integration, receipt packet.

Likely modules: policy engine/context, metric catalog, payment intent service, new LNURL services/routes, business role checks, frontend `/payregister/lnurl`, SDK helpers, receipt/evidence packet docs/tests.

## 20. SDK Impact

Python audited: `sdk/python/bitcoin_bastion_sdk/access_auth.py`, `auth.py`, `signing.py`, `resources/access.py`, tests/readme. TypeScript audited: `sdk/typescript/src/auth.ts`, `http.ts`, `resources/access.ts`, utils/tests/examples.

Required support: wallet challenge helpers, BIP-322 hooks (not private key handling), LNURL-auth challenge/session helpers, LNURL-pay subscription helpers, Lightning Address resolution, LNURL-withdraw helper, PoP request signing, redaction, test vectors.

Hard requirements: SDK must not encourage `Authorization: Bearer <access_pass>`; must not log raw k1/signature/session/pass/recovery phrase/private key; must not ask for Bitcoin seed/private key.

## 21. Frontend / Reflex Impact

Required pages/components: `/wallet-auth`, `/wallet-auth/register`, `/wallet-auth/login`, `/wallet-auth/devices`, `/wallet-auth/step-up`, `/wallet-auth/recovery`, `/lnurl/login`, `/lnurl/pay`, `/lnurl/activate`, `/lnurl/withdraw`, `/payregister/lnurl`, Lightning Address display, QR generation, NFC link support if applicable.

Required copy:

- “This signature does not authorize a Bitcoin transaction.”
- “This signature only proves wallet control for Bastion access.”
- “Use a dedicated Bastion auth wallet/address.”
- “Do not use your cold treasury wallet for routine login.”
- “Bastion will never ask for your Bitcoin seed.”
- “LNURL-auth is not a Bitcoin transaction.”
- “LNURL-pay invoice creation is not payment settlement.”

## 22. CLI / Bot Impact

Future support: wallet-auth challenge, LNURL-auth QR creation, LNURL-pay subscription QR creation, Lightning Address lookup, LNURL withdraw request, device list, step-up, recovery start, lockdown.

Rules: no seed/private-key prompts; raw secrets redacted; QR payloads safe to display; bot access uses scoped child/delegated pass or policy decision.

## 23. Database Impact

Future tables expected: `wallet_principals`, `wallet_proofs`, `wallet_auth_challenges`, `wallet_devices`, `wallet_sessions`, `wallet_session_nonces`, `wallet_step_up_proofs`, `wallet_compatibility_records`, `recovery_capsules`, `multi_wallet_quorums`, `wallet_privacy_commitments`, `lnurl_auth_challenges`, `lnurl_auth_attempts`, `lnurl_principals`, `lnurl_pay_requests`, `lnurl_payment_proofs`, `lnurl_verify_checks`, `lnurl_withdraw_requests`, `lnurl_withdraw_attempts`, `lnurl_success_actions`, `lnurl_payer_data`, `lightning_addresses`.

Existing tables to extend: `subscription_entitlements`, metric usage/metric entitlements representation, policy decision records if added, `access_audit_events`, `access_revocations`, `access_certificates`, offline validity/delegated pass tables, PayRegister-related tables when present.

Rules: no raw Bitcoin seed/private key columns; no raw k1 if avoidable; no raw session token; no global user_id by default; no Lightning Address as auth identity.

## 24. Environment / Deployment Impact

Current config: `.env.example`, `app/core/config.py`, `docs/ACCESS_ENVIRONMENT.md`, Kubernetes base templates, and a values-only `helm/bitcoin-bastion` placeholder with no deployable templates.

Future variables: `WALLET_AUTH_ENABLED`, `WALLET_AUTH_REQUIRE_BIP322`, `WALLET_AUTH_ALLOW_LEGACY_SIGNATURES=false`, challenge/session TTLs, dedicated address warning, sovereign mode, wallet server pepper, `LNURL_ENABLED`, `LNURL_AUTH_ENABLED`, `LNURL_PAY_ENABLED`, `LNURL_WITHDRAW_ENABLED`, `LNURL_VERIFY_ENABLED`, callback base URLs, domain, min/max sendable msat, `LNURL_K1_TTL_SECONDS`, `LNURL_REQUIRE_SETTLEMENT_VERIFY=true`, `LNURL_ALLOW_PAYERDATA_EMAIL=false`, `LNURL_ALLOW_LEGACY_HTTP_ONION=false` or documented policy.

Rules: no real secrets; legacy signatures disabled by default; payerData email disabled by default; settlement verify required by default.

## 25. OpenAPI / Contract Impact

Audit targets: `app/api/openapi.py`, `tests/contract/test_access_openapi_contract.py`, `tests/test_openapi_contract.py` if present, `docs/OPENAPI_STABILITY.md` if present.

Future OpenAPI surfaces: wallet-auth endpoints, LNURL-auth endpoints, LNURL-pay endpoints, LNURL-verify endpoint, LNURL-withdraw endpoints, Lightning Address well-known endpoint, PayRegister LNURL endpoints.

Hard requirements: no active password login; no bearer Access Pass as primary auth; no Bitcoin seed/private key input; LNURL callbacks documented clearly; response schemas safe and secret-free.

## 26. Security / Release Gate Impact

Existing gates cover disabled password auth, no bearer Access Pass, no Bitcoin seed auth, access policy required, recovery abuse, child key scope escalation, signature safety, and OpenAPI contract.

Future gates must fail if wallet signature alone grants full access; LNURL-auth alone grants full access; k1 reused/expired/unexpected accepted; invoice generation issues entitlement; valuable withdraw QR issued before policy; Lightning Address treated as identity; payerData email required; comment authorizes; successAction leaks; seed/private key accepted; protected endpoint bypasses policy; SDK/frontend uses bearer Access Pass; OpenAPI advertises invalid model.

## 27. Migration Risk Register

| risk | affected files | severity | likelihood | mitigation | required tests | owner/module |
|---|---|---:|---:|---|---|---|
| wallet-only access mistake | access dependencies, policy, wallet APIs | Critical | Medium | Require device+PoP+policy+entitlement | wallet proof alone denied | Access/Auth |
| LNURL-auth treated as full authorization | LNURL auth service/router | Critical | High | Auth maps to principal proof only | lnurl-auth alone denied | LNURL/Auth |
| k1 replay | k1 registry/callback | Critical | Medium | single-use hash registry | reused k1 rejected | LNURL/Auth |
| k1 not bound to action/domain | challenge service | High | Medium | bind domain/action/intent | wrong action/domain rejected | LNURL/Auth |
| auth domain migration duplicate principals | principal service | High | Medium | domain policy + stable HMAC ids | migration collision tests | Identity |
| invoice generated treated as paid | lnurl-pay/entitlement | Critical | Medium | verify settlement gate | no entitlement on invoice | Payments |
| withdraw k1 theft | lnurl-withdraw | Critical | Medium | auth/policy before valuable QR | stolen k1 denied | Payments/Risk |
| payerData privacy leak | schemas/audit/logs | High | Medium | minimal fields/redaction | no raw payerData PII by default | Privacy |
| Lightning Address treated as identity | principal/policy | High | Medium | routing UX only | address cannot authorize | LN Address |
| legacy Bitcoin signature high-risk | BIP-322 fallback | High | Medium | disabled by default/low strength | fallback denied high-risk | Wallet Proof |
| BIP-322 verifier incomplete | verifier | Critical | Medium | interface + vectors before prod | known vectors pass/fail | Crypto |
| fake PQ support | issuer metadata/docs | High | Medium | truth-in-crypto labels | no PQ claim without implementation | Crypto |
| raw wallet address leakage | audit/logs/db/sdk | High | Medium | HMAC/fingerprints | redaction scan | Privacy |
| raw k1/signature/session leakage | LNURL/session/audit | Critical | Medium | hash/redact | sensitive-material scan | Security |
| seed/private key input introduced | APIs/SDK/frontend | Critical | Low | denylist/validation/copy | seed/private key rejected | Security |
| PayRegister refund abuse | withdraw/refund policy | Critical | Medium | refund policy, limits, cooldown | refund requires policy | PayRegister |
| SDK bearer fallback | SDK auth/http/examples | High | Medium | fail closed/no Authorization | SDK no bearer tests | SDK |
| frontend old login form remains | frontend/reflex | High | Medium | remove/disable legacy forms | no password form tests | Frontend |
| OpenAPI mismatch | openapi/contracts | High | Medium | contract tests | OpenAPI auth model tests | API |
| release gate missing | tests/docs/CI | Critical | Medium | final 72/72 gate | all above in CI | Release |

## 28. New Prompt Sequence Impact

Updated sequence summary:

0/72 Wallet-first + LNURL migration audit; 1/72 Wallet-first ADR; 2/72 Wallet-first + LNURL threat model; 3/72 Wallet + LNURL auth domain package; 4/72 Wallet + LNURL schemas; 5/72 Wallet + LNURL DB models; 6/72 Wallet + LNURL Alembic migration; 7/72 Wallet privacy commitments; 8/72 Structured Bastion Auth Intent; 9/72 Wallet challenge service; 10/72 Wallet proof verifier interface; 11/72 BIP-322 verifier; 12/72 Legacy Bitcoin message signature fallback; 13/72 Hardware wallet proof metadata; 14/72 Wallet compatibility registry; 15/72 Wallet Principal service; 16/72 Wallet device binding service; 17/72 Wallet session service; 18/72 Wallet PoP request verifier; 19/72 Bastion LNURL domain package; 20/72 LNURL encoding / decoding / URL safety; 21/72 LNURL k1 registry and replay protection; 22/72 LNURL-auth challenge service; 23/72 LNURL-auth callback verifier; 24/72 Lightning Principal service; 25/72 LNURL-auth session bridge; 26/72 LNURL-auth step-up service; 27/72 LNURL-auth audit events; 28/72 LNURL-pay subscription request service; 29/72 LNURL-pay metadata builder; 30/72 LNURL-pay callback invoice service; 31/72 LNURL-verify settlement service; 32/72 LNURL payment proof service; 33/72 LNURL payment to subscription entitlement binding; 34/72 LNURL successAction activation service; 35/72 LNURL commentAllowed handling; 36/72 LNURL payerData.auth binding; 37/72 Lightning Address service; 38/72 /.well-known/lnurlp routes; 39/72 Product Lightning Addresses; 40/72 PayRegister LNURL-pay static QR; 41/72 PayRegister cashier / shift metadata; 42/72 Merchant Lightning Address; 43/72 LNURL receipt packet; 44/72 LNURL-withdraw request service; 45/72 LNURL-withdraw callback verifier; 46/72 Refund / payout policy integration; 47/72 PayRegister refund via LNURL-withdraw; 48/72 Withdraw audit and risk limits; 49/72 Wallet-bound Subscription Entitlements; 50/72 Lightning Principal policy actor types; 51/72 LNURL Policy Engine hooks; 52/72 Wallet + LNURL Step-Up policy; 53/72 Wallet + LNURL Revocation extensions; 54/72 Wallet + LNURL Audit Chain events; 55/72 Access Integrity Score 2.0 with LNURL signals; 56/72 Wallet + LNURL observability metrics; 57/72 Recovery Capsule foundation; 58/72 LNURL-auth as recovery factor; 59/72 Multi-wallet / multi-method quorum; 60/72 Access Certificate bridge for wallet/LNURL principals; 61/72 Offline validity pack bridge; 62/72 PQ issuer metadata for LNURL-bound objects; 63/72 Transparency checkpoints for wallet/LNURL auth; 64/72 Wallet Auth API router; 65/72 LNURL API router; 66/72 Wallet + LNURL auth dependencies; 67/72 Python SDK wallet + LNURL auth; 68/72 TypeScript SDK wallet + LNURL auth; 69/72 CLI wallet + LNURL auth; 70/72 Frontend wallet + LNURL auth flow; 71/72 Reflex wallet + LNURL auth flow; 72/72 Final Wallet-first + LNURL production release gate.

## 29. Audit Acceptance Criteria

- [x] `docs/WALLET_LNURL_AUTH_MIGRATION_AUDIT.md` exists.
- [x] Current Access Layer surfaces are mapped.
- [x] Legacy auth residue is mapped.
- [x] Wallet-first integration points are mapped.
- [x] LNURL-auth/pay/Lightning Address/withdraw/verify requirements are mapped.
- [x] payerData/successAction/commentAllowed requirements are mapped.
- [x] Policy, Audit Chain, Revocation, Recovery/Quorum impacts are mapped.
- [x] PayRegister, SDK, frontend, CLI impacts are mapped.
- [x] DB/env/OpenAPI/security impacts are mapped.
- [x] Migration risk register exists.
- [x] Updated 0/72 prompt sequence is included.
- [x] No runtime behavior changed; no migrations, routes, fake LNURL, fake BIP-322, or fake PQ implementation added.

## 30. Validation Commands

Commands requested for repository-safe validation. Results must be interpreted as audit validation only because this prompt intentionally changed documentation only.

- `pytest tests/test_openapi_contract.py` — run attempted if file exists; see final response for actual result.
- `pytest tests/test_api_contracts.py` — run attempted if file exists; see final response for actual result.
- `pytest tests/security/ -q` — run attempted; see final response for actual result.
- `pytest tests/test_release_gates.py` — run attempted if file exists; see final response for actual result.
- `ruff check .` — run attempted; see final response for actual result.
- `mypy app sdk` — run attempted if mypy configured/available; see final response for actual result.

## 31. Final Response Required Checklist

Final response should include: files created, files inspected, current Access Layer summary, legacy auth residue summary, wallet-first integration summary, LNURL integration summary, PayRegister integration summary, top 10 migration risks, validation commands run, failures/limitations, and next prompt: **Prompt 1/72**.
