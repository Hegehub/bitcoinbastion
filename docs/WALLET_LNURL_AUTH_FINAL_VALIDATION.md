# Wallet/LNURL Auth Final Validation

**Evidence date:** 2026-08-03  
**Decision:** **NOT PRODUCTION-READY**

## 1. Architecture

The implemented target is Wallet or LNURL proof → pseudonymous Principal → Device Binding → short-lived PoP Session → signed request with nonce/timestamp/body binding → Subscription/Metric Entitlements → Policy Engine. Audit, Revocation, Recovery Capsule, Step-Up, Quorum, optional Access Certificate/Offline Pack, crypto-agile issuer metadata, and transparency are independent layers.

Wallet proof is not authorization. LNURL is an adapter, not authorization. Payment proves settlement, not login. Lightning Address is routing, not identity. Recovery accepts no Bitcoin seed/private material.

## 2. Status matrix

| Area | Status | Evidence / limitation |
|---|---|---|
| Legacy password/bearer prohibition | IMPLEMENTED | Disabled legacy routes and security tests; PoP scheme required. |
| Bitcoin/Lightning Principals and privacy commitments | IMPLEMENTED | Separate hashed identifiers and policy contexts; no email requirement. |
| BIP-322 | PARTIAL | Verification, intent/network/replay tests exist; repository evidence does not establish universal wallet/script interoperability. |
| Device Binding / PoP / replay | IMPLEMENTED | Ed25519 Device keys, canonical request binding, nonce and freshness tests. |
| Policy, subscription, metric entitlements | IMPLEMENTED | Central policy and denial tests cover subscription/metric separation. |
| LNURL-auth/k1 | PARTIAL | Challenge/callback/signature/replay services are tested; production API composition defaults fail closed and no auth-attempt status API exists for clients. |
| Stable LNURL auth domain | BLOCKED | Policy documented, but no production domain/configuration evidence is recorded. |
| LNURL-pay/verify/entitlement | IMPLEMENTED | Settlement-gated, idempotent proof/entitlement service tests exist. Provider production credentials/evidence are absent. |
| Lightning Address / payerData / comment / successAction | IMPLEMENTED | Privacy, metadata-not-authorization, URL and well-known route tests exist. |
| LNURL-withdraw | PARTIAL | Policy, limits, k1 callback, double-payment and role tests exist; no API status route and production payout evidence is absent. |
| PayRegister LNURL | PARTIAL | Static QR, shift/context and refund-risk tests exist; no production merchant/provider evidence. |
| Recovery / quorum / lockdown / revocation / audit | IMPLEMENTED | Security and integration tests cover factors, cooldown, role/quorum, cascades, chain tampering and redaction. |
| Access Certificate / Offline Validity Pack | IMPLEMENTED | Non-bearer, Principal/Device binding and forbidden offline action tests exist. |
| PQ readiness | PARTIAL | Crypto-agile/versioned metadata and issuer-chain interfaces exist. ML-DSA, SLH-DSA and ML-KEM are **not proven enabled**. Claim only “PQ-ready interfaces.” |
| Transparency | IMPLEMENTED | Sequence, sensitive-data and integration tests exist; no external production publication evidence. |
| Tor/Onion LNURL | NOT IMPLEMENTED | Do not claim anonymity or weaken URL safety. |
| Frontend end-to-end auth | BLOCKED | Missing auth-status API and deployment non-exportable browser/Vault Device signer bridge. |
| Deployment | BLOCKED | No clean production migration, ingress/auth-domain, secret-manager, provider settlement, burn-in or wallet interoperability evidence was executed here. |

## 3. Endpoint coverage

Wallet router implements challenges, register, login, sessions, step-up, Principal, entitlements, devices, wallet bindings, Lockdown, and Recovery Capsule endpoints under `/api/v1/wallet-auth`. LNURL router implements auth challenge/callback/session/step-up, pay subscription/callback/verify, and withdraw request/callback. `/.well-known/lnurlp/{name}` implements discovery. Missing client-facing auth-attempt status and withdraw-status endpoints are release blockers for complete web/CLI orchestration.

## 4. Attack scenarios

| Scenario | Expected / evidence status |
|---|---|
| Stolen `.bbp` | Denied without Device/possession proof — tested. |
| Stolen session id | Cannot forge PoP signature — tested. |
| Wallet signature or k1 replay | Rejected — tested. |
| Invoice without settlement | No entitlement — tested. |
| Duplicate settlement | Single proof/transition — tested at service level. |
| Stolen withdraw QR | k1, amount, authorization and policy remain enforced — tested at service level. |
| Cashier/browser compromise | Cannot gain owner/high assurance solely from class/UI — tested. |
| Revoked Principal | Policy/session/delegation cascade denies access — tested. |
| Support recovery bypass | Denied; quorum/cooldown retained — tested. |
| Seed entered in generic protected input | Rejected/redacted by safety boundaries; no auth schema accepts it — tested. |

## 5. Test matrix

The required candidate gate is `make wallet-lnurl-auth-release-gate`. It runs all security tests, focused OpenAPI/contracts, end-to-end service integrations, Python and TypeScript SDK suites, CLI tests, Reflex tests/build, and release-governance tests. `scripts/wallet-lnurl-auth-release-gate.sh --production` intentionally exits non-zero while blockers remain.

## 6. Repository-wide terminology audit

The release audit classified password/JWT/Bearer references in active authentication dependencies as disabled migration boundaries that fail closed; their remaining positive uses are rejection tests, deprecated compatibility documentation, or unrelated provider credentials. `user_id` remains in pre-wallet application domains and legacy database models, but Wallet/LNURL Principal contracts use pseudonymous hashes and do not expose a global cross-product identity. Seed, mnemonic, xprv and private-key terms occur in prohibitions, redaction/safety guards, test fixtures, or Bastion Device/issuer-key implementations—not wallet-secret input schemas. Broad-scope and bypass terms occur in forbidden-scope enforcement or negative tests. This classification does not certify unreviewed third-party code or deployment state.

## 7. Residual risks and production decision

Production promotion is blocked by: unconfigured fail-closed production API composition boundaries; absent stable production auth-domain evidence; missing LNURL auth/withdraw status contracts; absent browser non-exportable Device signer bridge; no clean production database migration/rollback evidence in this run; no provider/BTCPay production settlement evidence; no production ingress/secret-manager/alert/burn-in evidence; and no real-wallet compatibility matrix. The broad integration regression run also exposes stale legacy-admin test overrides (`tests/integration/test_api_routes.py`) that receive the correct PoP-era `401` instead of the old expected `200`; the focused protected-route tests pass, but the broad suite is not green until that test is migrated to explicit policy contexts.

Passing repository tests proves a strong **release-candidate implementation**, not deployed-system assurance. Final classification is **NOT PRODUCTION-READY**.
