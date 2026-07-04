# Access Auth Migration Audit

Date: 2026-06-30  
Scope: audit-only production migration inventory for replacing legacy email / username / password / bearer-token auth with Bastion Proof-of-Access Auth. No runtime behavior was changed.

## 1. Executive Summary

Bitcoin Bastion currently contains an active legacy auth model centered on:

- `POST /api/v1/auth/register` with mandatory `email`, `username`, and `password`.
- `POST /api/v1/auth/login` with `username` and `password`.
- Argon2 password hashing through `passlib`.
- JWT creation with `python-jose`.
- protected API dependencies that require `Authorization: Bearer <token>`.
- a global `User` table used as auth identity and as ownership/actor identity across wallet, watchlist, treasury, admin, plugin, webhook, and user endpoints.
- SDK helpers that inject `Authorization: Bearer <api_key>`.
- bot runtime helpers that can call protected admin APIs with a bearer token.

This model must be replaced because the target Bastion Proof-of-Access architecture explicitly forbids mandatory email, password login, classic account registration, bearer Access Pass semantics, backend private keys as auth roots, and Bitcoin seed/private key authentication. The replacement must derive access from payment proof, issuer-signed entitlements, device-key proof of possession, origin-bound challenges, policy decisions on every protected request, revocation checks, and audit-chain recording.

Audit totals from repository scans:

| Metric | Count | Notes |
|---|---:|---|
| Legacy auth files found | 42 | Files matching active legacy auth classes/dependencies/hash/JWT/bearer patterns. |
| Bearer/JWT/token usage files found | 131 | Includes runtime, SDK, tests, docs, safety redaction, deployment examples, and storage warnings. |
| Frontend auth assumption files found | 13 | `frontend/` is absent; `reflex_frontend/` has route/dashboard assumptions and safe-logging token examples. |
| SDK auth assumption files found | 17 | Python and TypeScript SDK source, tests, examples, and docs. |
| Tests impacted | 50 | Includes direct auth tests plus protected endpoint/SDK/bot/redaction/OpenAPI-style contract coverage. |

## 2. Current Auth Surface Map

### Active backend auth files

| File | Classes / functions / schemas / behavior | Migration disposition |
|---|---|---|
| `app/api/v1/auth.py` | `register`, `login`; exposes legacy auth router under `/auth`. | Freeze, deprecate, later disable/remove. |
| `app/schemas/auth.py` | `RegisterRequest`, `LoginRequest`, `TokenResponse`. | Replace with Access challenge/session schemas. |
| `app/schemas/user.py` | `UserOut` exposes `email`, `username`, role/active flags. | Keep only if user profile remains non-auth; remove from auth flow. |
| `app/services/auth/auth_service.py` | `AuthService.register`, `AuthService.login`; hashes passwords and issues tokens. | Remove after Access Layer cutover. |
| `app/core/security.py` | `hash_password`, `verify_password`, `create_access_token`, JWT/passlib context. | Remove password/JWT auth pieces; keep non-auth security headers if still needed. |
| `app/api/dependencies.py` | `decode_user_id_from_token`, `get_current_user`, `get_admin_user`; bearer/JWT validation. | Replace with Proof-of-Possession + Policy Engine dependencies. |
| `app/db/models/auth.py` | `User`, `SubscriptionPlan`, `UserSubscription`. | Migrate auth identity to Access models; evaluate subscriptions as entitlement source. |
| `app/db/repositories/user_repository.py` | User CRUD and lookup by username/id. | Replace auth lookups with entitlement/session/device repositories. |
| `app/core/config.py` | JWT settings and production secret guards. | Replace JWT settings with Access Layer variables. |
| `app/db/migrations/versions/20260413_0001_initial.py` | Creates `users` with `email`, `username`, `hashed_password`, `last_login_at`; creates subscriptions. | Do not edit now; future migration removes/disables auth columns. |
| `app/db/migrations/versions/20260413_0002_expand_domain_models.py` | Adds `user_id` fields to domain tables. | Requires Access identity/subject mapping migration. |
| `app/db/migrations/versions/9ecab5c090cf_align_models_schema_truth.py` | Index alignment for `user_id`/actor fields. | Revisit after Access subject model. |

### Protected API files and endpoints using legacy dependencies

| File | Protected dependency / identity assumption | Endpoints or behavior |
|---|---|---|
| `app/api/v1/admin.py` | `get_admin_user` | Admin status/jobs/recovery endpoints. |
| `app/api/v1/users.py` | `get_current_user` | list users and `/me`. |
| `app/api/v1/wallet.py` | `get_current_user`, `current_user.id` | wallet profile create/get/list. |
| `app/api/v1/entities.py` | `get_current_user`, `get_admin_user`, watchlist `user_id` | watchlist and admin entity operations. |
| `app/api/v1/policy.py` | `get_admin_user` | policy CRUD/evaluation admin operations. |
| `app/api/v1/treasury.py` | `get_current_user`, `get_admin_user`, actor IDs | treasury request/approval/rejection/list paths. |
| `app/api/v1/plugins.py` | `get_admin_user` | plugin enable/disable/execute admin paths. |
| `app/api/v1/webhooks.py` | `get_admin_user` | webhook endpoint/subscription/test/delivery management. |

### SDK, frontend, bot, CLI, MCP surfaces

| Area | Files | Current assumption |
|---|---|---|
| Python SDK | `sdk/python/bitcoin_bastion_sdk/auth.py`, `transport.py`, `client.py`, `async_client.py`, tests, README | Optional `api_key` is sent as `Authorization: Bearer`. |
| TypeScript SDK | `sdk/typescript/src/auth.ts`, `http.ts`, `config.ts`, examples, tests, README | Optional `apiKey` is sent as `Authorization: Bearer`. |
| Reflex frontend | `reflex_frontend/` | No active password form found; route/dashboard docs/tests include `/register`, console route assumptions, and safe-logging examples for bearer/API keys. |
| `frontend/` | absent | No Next.js `frontend/` directory exists in current checkout. Docs still mention historical frontend routes. |
| Bot | `app/bot/handlers/runtime_actions.py`, `app/bot/runner.py`, tests | Runtime actions can use bearer token from config/env to call admin APIs. |
| CLI | `cli/bastion_cli/config.py`, `main.py`, docs/tests | API URL/config and some token/auth assumptions in CLI docs/tests need review. |
| MCP | `mcp/bastion_mcp/client.py`, `config.py`, README/tests | API client/auth configuration needs migration to Proof-of-Access headers or delegated pass. |

## 3. Current API Auth Endpoints

| File | Route path | Function | Request schema | Response schema | Issues bearer/JWT/token? | Replacement strategy |
|---|---|---|---|---|---|---|
| `app/api/v1/auth.py` | `POST /api/v1/auth/register` | `register` | `RegisterRequest` (`email`, `username`, `password`) | `UserOut` | No token issuance, but creates password-backed user. | Disable after Access signup/import path exists; replace with payment-proof/access-pass import or entitlement creation endpoint. |
| `app/api/v1/auth.py` | `POST /api/v1/auth/login` | `login` | `LoginRequest` (`username`, `password`) | `TokenResponse` (`access_token`, `token_type=bearer`) | Yes; `AuthService.login` returns JWT bearer token. | Replace with origin-bound challenge issuance, device-key signed challenge verification, and Proof-of-Possession session issuance. |
| `app/api/v1/users.py` | `GET /api/v1/users/me` | `me` | bearer header through dependency | `ResponseEnvelope[UserOut]` | Consumes bearer/JWT via `get_current_user`. | Replace with current Access subject/session endpoint returning entitlement/session/device context. |
| `app/api/dependencies.py` | all protected routes | `get_current_user` / `get_admin_user` | `Authorization: Bearer <jwt>` header | `User` object | Consumes bearer/JWT. | Replace with `get_access_session`, `require_policy_decision`, and admin capability policy checks. |

## 4. Current Auth Data Model

| Model / table / migration | Fields / purpose | Current auth role | Disposition |
|---|---|---|---|
| `User` / `users` in `app/db/models/auth.py` | `email`, `username`, `hashed_password`, `is_active`, `is_admin`, `role`, preferences/timezone, timestamps, `last_login_at`. | Primary legacy auth identity and admin role source. | Migrate/replace for auth. Keep profile/preferences only if decoupled from access identity. Remove/disable password/email/username as required auth fields. |
| `SubscriptionPlan` / `subscription_plans` | plan code/name/features/limits. | Billing/capability placeholder attached to legacy user. | Migrate into Access entitlement catalog or keep as non-auth product catalog if policy uses it. |
| `UserSubscription` / `user_subscriptions` | `user_id`, `plan_id`, status, provider IDs. | Subscription bound to legacy user ID. | Replace with issuer-signed entitlement and payment-proof/subscription mapping. |
| `WalletProfile` / `wallet_profiles` | `user_id` FK. | User-owned wallet profile. | Replace owner with access subject/workspace/entitlement subject; do not bind to global user ID by default. |
| `WatchedEntity` / `watched_entities` | nullable `user_id` FK. | Watchlist ownership. | Replace with access subject/workspace scoped ownership. |
| `AuditLog` / `audit_logs` | `actor_user_id`. | Legacy actor identity. | Migrate to audit-chain actor/session/device/entitlement fingerprint. |
| `DeliveryLog` / `delivery_logs` | nullable `user_id`. | Optional legacy user association. | Migrate to subject/workspace/delegated pass identifiers. |
| Initial/expand/index migrations | `20260413_0001_initial.py`, `20260413_0002_expand_domain_models.py`, `9ecab5c090cf_align_models_schema_truth.py`. | Persist legacy user/password and user_id relationships. | Leave untouched during audit; future migrations must explicitly migrate/retire these. |

## 5. Current Token / JWT / Bearer Usage

Repository scan found 131 files mentioning bearer/JWT/token-related terms. Classification:

### Active runtime auth path

- `app/api/dependencies.py`: validates `Authorization: Bearer`, decodes JWT, resolves `User`.
- `app/services/auth/auth_service.py`: creates JWT access token after password login.
- `app/core/security.py`: JWT encode and password helpers.
- `app/core/config.py`: JWT secret/algorithm/issuer/TTL settings and guards.
- `app/bot/handlers/runtime_actions.py`: builds `Authorization: Bearer` for admin runtime API calls.

Migration risk: high. These are the active legacy auth paths that can continue accepting passwords/bearer tokens unless frozen and replaced.

### SDK helper paths

- Python: `sdk/python/bitcoin_bastion_sdk/auth.py`, `transport.py`, `client.py`, `async_client.py`, `README.md`, `tests/test_client.py`, `tests/conftest.py`.
- TypeScript: `sdk/typescript/src/auth.ts`, `src/http.ts`, `src/config.ts`, examples, README, `tests/client.test.ts`.

Migration risk: high. SDKs normalize bearer-token usage for integrators.

### Test-only fixtures / assertions

- `tests/unit/test_auth_dependencies.py`, `tests/unit/test_auth_service.py` directly validate legacy auth.
- `tests/unit/test_bot_runtime_actions.py` validates bot bearer header behavior.
- Contract/integration tests for admin/plugin/webhook/runtime APIs depend on bearer/admin dependency behavior.
- Redaction/safety tests include token/password/API-key strings and must remain but may need Access Pass/session terminology.

Migration risk: medium/high. Tests will either block removal or mask retained bearer behavior if not rewritten.

### Documentation / deployment references

Docs and manifests mention JWT, bearer tokens, API keys, secrets, auth headers, token redaction, and operations curl examples. Important files include `README.md`, `.env.example`, `docs/API_CONTRACTS.md`, `docs/OPERATIONS_RUNBOOK.md`, `docs/SECURITY.md`, `docs/ENVIRONMENT_VARIABLES.md`, `docs/SDK_INTEGRATION_STATUS.md`, `docs/DEVELOPER_API.md`, `docs/CLI.md`, `docs/MCP_CONNECTOR.md`, `docs/FRONTEND_API_CLIENT_CONTRACT.md`, `docs/STORAGE_LAYER_ARCHITECTURE.md`, `docs/STORAGE_OUTBOX.md`, and deployment secret templates under `deploy/`, `k8s/`, and `helm/`.

Migration risk: medium. OpenAPI/docs may advertise disabled auth if not updated.

### Safety/redaction/non-auth token mentions

Many storage, event, webhook, logging, ClickHouse, metric-usage, and evidence files mention `token`, `api_key`, `password`, or `authorization` as sensitive-material filters. These are not legacy auth implementation, but must remain or be expanded for Access Pass/session headers.

Migration risk: low/medium. Do not remove safety filters; add `X-Bastion-*`, Access Pass, session, nonce, signature, and entitlement secret names.

## 6. Current Protected Endpoint Dependencies

| Dependency/helper | File | Behavior | Endpoints using it | Replacement needed |
|---|---|---|---|---|
| `decode_user_id_from_token` | `app/api/dependencies.py` | Decodes JWT with configured secret/algorithm/issuer and extracts integer `sub`. | Used by `get_current_user`. | Verify Proof-of-Possession session, challenge origin, nonce, body hash, signature, session TTL, revocation state. |
| `get_current_user` | `app/api/dependencies.py` | Requires `Authorization` header starting with `Bearer `, loads `User` by ID. | wallet, users, entities watchlist, treasury request/list. | `get_access_context` returning entitlement/session/device/workspace/policy subject. |
| `get_admin_user` | `app/api/dependencies.py` | Requires current user and checks `is_admin` and `role == admin`. | admin, entities admin, policy, treasury approvals, plugins, webhooks. | `require_policy("admin:*")` or capability-based policy decision over Access entitlement. |
| Bot admin bearer builder | `app/bot/handlers/runtime_actions.py` | Adds `Authorization: Bearer <token>` when token exists. | Bot runtime admin commands/actions. | Delegated Telegram child-pass/session-bound signed requests. |
| SDK auth header builders | SDK files | Adds bearer headers. | All SDK resource calls using transport/http helpers. | Request signer emitting `X-Bastion-Session`, `X-Bastion-Timestamp`, `X-Bastion-Nonce`, `X-Bastion-Body-Hash`, `X-Bastion-Signature`. |

## 7. SDK Auth Audit

### Python SDK

- `sdk/python/bitcoin_bastion_sdk/auth.py` merges caller headers and, if `api_key` is provided, sets `Authorization: Bearer <api_key>`.
- `sdk/python/bitcoin_bastion_sdk/transport.py` calls `build_headers` for sync and async transports.
- `sdk/python/bitcoin_bastion_sdk/client.py` and `async_client.py` expose `api_key` constructor arguments.
- `sdk/python/tests/test_client.py` asserts the bearer header is sent and not leaked in exception text.
- `sdk/python/README.md` documents bearer token behavior.

Current signing: none. Requests are not body-hash signed, nonce-protected, timestamped, origin-bound, or possession-proven by the SDK.

Required migration:

- Replace `api_key` with Access session/device signer configuration.
- Add canonical request construction and `X-Bastion-*` headers.
- Preserve redaction tests but update sensitive names to Access sessions/signatures.
- Add replay/body tamper tests.

### TypeScript SDK

- `sdk/typescript/src/auth.ts` returns `{ Authorization: `Bearer ${apiKey}` }`.
- `sdk/typescript/src/http.ts` spreads `authHeaders(this.config.apiKey)` into every request.
- `sdk/typescript/src/config.ts` exposes `apiKey`.
- examples and README use `BASTION_API_KEY`.
- `sdk/typescript/tests/client.test.ts` asserts `Authorization: Bearer token`.

Current signing: none.

Required migration:

- Replace `apiKey` config with session ID + device key signer or callback.
- Emit `X-Bastion-Session`, `X-Bastion-Timestamp`, `X-Bastion-Nonce`, `X-Bastion-Body-Hash`, `X-Bastion-Signature`.
- Add deterministic canonicalization and browser/node crypto support.

## 8. Frontend Auth Audit

`frontend/` is absent in the current repository checkout. `reflex_frontend/` exists.

| Item | Files | Finding | Classification |
|---|---|---|---|
| Login forms | `reflex_frontend/` scan | No active `login` form/password input found outside docs/tests/safe logging. | No removal required now; add regression gate. |
| Register route assumptions | `docs/FRONTEND_REFLEX_MIGRATION_BASELINE.md`, `docs/FRONTEND_ROUTES.md`, route tests/docs | Historical or route inventory references `/register`. | Replace with Access Pass import / payment access flow or mark deprecated. |
| Token storage | `reflex_frontend/` scan | No `localStorage`/`sessionStorage` token storage found in current results. | Keep as public/no-auth; add no-token-storage test. |
| Bearer/API key logging examples | `reflex_frontend/tests/test_safe_logging.py`, `reflex_frontend/bastion_ui/security/safe_logging.py` | Redacts `Authorization: Bearer` and API keys. | Keep redaction; extend to `X-Bastion-*`. |
| Protected dashboard/console assumptions | `reflex_frontend/bastion_ui/app.py`, console route tests, docs | Console/dashboard routes are route-registered but not wired to legacy login in scan. | Replace with challenge/session-protected route guards when Access UI exists. |
| API client assumptions | `reflex_frontend/bastion_ui/tests/test_api_client.py`, state modules | API call tests exist; no bearer injection found in targeted scan. | Requires review when Access headers are introduced. |

## 9. Bot / Telegram Auth Audit

| File | Finding | Migration path |
|---|---|---|
| `app/bot/handlers/runtime_actions.py` | Builds `Authorization: Bearer <token>` for runtime/admin calls and exposes operational actions. | Replace with Telegram child-pass or scoped delegated pass; every bot action must call policy decision with Telegram binding, entitlement scope, command, and target resource. |
| `app/bot/runner.py` | Uses Telegram bot token/runtime config. | Keep Telegram platform token for bot transport, but do not treat it as product authorization. |
| `tests/unit/test_bot_runtime_actions.py` | Validates legacy admin bearer behavior. | Replace with delegated pass/session signature tests and policy-denied cases. |
| Delivery services | `app/services/delivery/publish_service.py`, `telegram_delivery.py` | Telegram bot token used for outbound delivery, not user auth. | Keep as delivery secret; ensure redaction and no entitlement decision from bot token alone. |

Migration target: Telegram user binding should create or reference a child-pass/delegated pass; commands should be scoped by entitlement and checked by Policy Engine before any protected API action. Bot logs must not contain raw passes, sessions, signatures, or Telegram tokens.

## 10. Test Suite Impact

| Category | Files | Replacement tests |
|---|---|---|
| Password login/register | `tests/unit/test_auth_service.py`, API route/contract tests around `/auth/register` and `/auth/login`. | Challenge/session issuance tests, no password schemas, no login/register OpenAPI tests. |
| Bearer token dependencies | `tests/unit/test_auth_dependencies.py`, protected admin/entity/treasury/webhook/plugin tests. | Proof-of-Possession dependency tests: missing headers, bad nonce, stale timestamp, bad body hash, bad signature, revoked session. |
| Mock/current user | Integration/contract tests using admin/current user fixtures or legacy tokens. | Access context fixtures with entitlement/capability/policy decisions. |
| Protected endpoints | `tests/integration/test_admin_recovery_api.py`, `test_admin_job_runs.py`, `test_entities_api.py`, `test_treasury_admin_guards.py`, contract plugin/webhook/runtime tests. | Verify Policy Engine scopes for each protected endpoint. |
| SDK auth tests | `sdk/python/tests/*`, `sdk/typescript/tests/client.test.ts`. | Verify `X-Bastion-*` signer headers, canonicalization, redaction, replay prevention. |
| Frontend auth tests | `reflex_frontend/tests/test_safe_logging.py`, route tests. | Add no-login/no-password/no-token-storage tests and Access import/challenge route tests. |
| OpenAPI/contract tests | `tests/test_api_contracts.py` if present, `tests/test_openapi_contract.py` if present, `docs/API_CONTRACTS.md`. | Assert no password login/register endpoints after disable stage and Access endpoints documented. |
| Security tests | `tests/security/test_metric_usage_no_sensitive_material.py`, storage/event redaction tests. | Extend sensitive material denylist to raw Access Pass, session, nonce/signature/private key fields; add `test_no_password_auth.py` and `test_no_bearer_access_pass.py`. |

## 11. Documentation Impact

| Doc/file group | Legacy mentions | Classification |
|---|---|---|
| `README.md` | Auth/project overview and environment/development references. | Must update. |
| `.env.example` | JWT/secret-related environment values. | Must update when variables change. |
| `docs/API_CONTRACTS.md` | Lists `/api/v1/auth/register` and `/api/v1/auth/login`. | Must update and eventually remove legacy contract. |
| `docs/OPERATIONS_RUNBOOK.md` | Uses `Authorization: Bearer <ADMIN_TOKEN>` curl examples and JWT secret startup notes. | Must update. |
| `docs/SECURITY.md`, `docs/DEPLOYMENT_SECURITY.md`, `docs/SECRETS_MANAGEMENT.md` | JWT/API key/password/security-secret guidance. | Must update. |
| `docs/SDK_INTEGRATION_STATUS.md`, `docs/DEVELOPER_API.md`, `docs/CLI.md`, `docs/MCP_CONNECTOR.md` | SDK/API-key/auth assumptions. | Must update. |
| `docs/FRONTEND_*`, `docs/FRONTEND_ROUTES.md`, `docs/FRONTEND_REFLEX_MIGRATION_BASELINE.md` | `/register`, dashboard/protected-route assumptions. | Must update or mark historical. |
| Storage/event docs | Warnings about raw tokens/bearer Access Pass/API keys/passwords. | Keep and extend; do not delete safety warnings. |
| Historical audit/readiness docs | e.g. final audits noting JWT + Argon2 baseline. | Can keep as historical if clearly dated; add superseding note. |
| Deployment manifests/docs | `deploy/`, `k8s/`, `helm/` secret templates and docs. | Must update JWT secrets to Access variables. |

## 12. Environment Variables Audit

### Current legacy/auth-relevant variables and config

| Variable/config | Location | Current role | Disposition |
|---|---|---|---|
| `JWT_SECRET_KEY` / `jwt_secret_key` | `.env.example`, `app/core/config.py`, deployment docs/templates | Signs/verifies JWT access tokens. | Remove after cutover; replace with Access issuer/session keys. |
| `JWT_ALGORITHM` / `jwt_algorithm` | config/env docs | JWT algorithm selection. | Remove with JWT auth. |
| `JWT_ISSUER` / `jwt_issuer` | config/env docs | JWT issuer claim. | Remove or replace with Access issuer ID metadata. |
| `JWT_ACCESS_TOKEN_EXPIRES_MINUTES` | config/env docs | Bearer token TTL. | Replace with `ACCESS_SESSION_TTL_SECONDS` and challenge TTL. |
| `TELEGRAM_BOT_TOKEN` | bot/delivery config | Telegram platform bot token, not product auth. | Keep as delivery/transport secret; never authorize product access alone. |
| `BASTION_API_KEY` | SDK examples/docs | SDK bearer token/API key. | Replace with session/device signer configuration. |
| `POSTGRES_PASSWORD`, object-store/ClickHouse/Qdrant keys | env/docs/deploy | Infrastructure secrets, not legacy app auth. | Keep, but redaction remains mandatory. |

### Future Access Layer variables to introduce later

- `ACCESS_SERVER_PEPPER`
- `ACCESS_ISSUER_KEY_ID`
- `ACCESS_ISSUER_PRIVATE_KEY`
- `ACCESS_SESSION_TTL_SECONDS`
- `ACCESS_CHALLENGE_TTL_SECONDS`
- `ACCESS_ALLOW_MANUAL_GRANTS`
- `ACCESS_BTCPAY_ENABLED`
- `ACCESS_BTCPAY_BASE_URL`
- `ACCESS_BTCPAY_API_KEY`
- `ACCESS_BTCPAY_STORE_ID`
- `ACCESS_BTCPAY_WEBHOOK_SECRET`

## 13. Migration Risk Register

| Risk | Affected files | Severity | Likelihood | Migration mitigation | Test required |
|---|---|---:|---:|---|---|
| Hidden bearer fallback | `app/api/dependencies.py`, SDKs, bot, CLI/MCP clients | Critical | High | Central removal gate; fail if `Authorization: Bearer` accepted on protected endpoints. | `tests/security/test_no_bearer_access_pass.py`. |
| Password auth accidentally retained | `app/api/v1/auth.py`, `app/services/auth/auth_service.py`, `app/core/security.py`, schemas | Critical | High | Freeze endpoints, remove schemas/service after Access cutover. | No `password` login/register OpenAPI paths. |
| Frontend still showing login/register form | `reflex_frontend/`, historical docs | High | Medium | Add route/UI scan and explicit Access import/challenge UX. | Frontend no password-input regression. |
| SDK still sending `Authorization: Bearer` | Python/TypeScript SDK auth/http files | Critical | High | Replace auth helpers with request signer APIs. | SDK tests assert only `X-Bastion-*` auth headers. |
| Protected endpoint missing Policy Engine | all protected API routers | Critical | High | Endpoint-by-endpoint migration checklist with deny-by-default dependency. | Per-router policy decision tests. |
| Old `User` model still treated as auth identity | models, repositories, user_id fields | Critical | High | Introduce Access subject/session/entitlement IDs; migrate ownership references. | DB/model tests deny User-as-auth dependency. |
| Logs leaking raw Access Pass | logging/redaction/storage/event code | Critical | Medium | Extend redaction denylist for Access Pass/session/signature headers. | Redaction tests with `X-Bastion-*`. |
| Token stored in browser | frontend API/client code | High | Medium | Store no bearer/pass material; use memory/session-bound key material where possible. | Frontend scan for local/session storage auth tokens. |
| Migration breaking public endpoints | API routers, Reflex public pages | Medium | Medium | Separate public/protected route inventory; public routes require no Access session. | Public endpoint no-auth regression suite. |
| OpenAPI still advertising password login | OpenAPI contract tests, docs | High | High | Contract gate after Stage 6. | OpenAPI no `/auth/login`/`RegisterRequest`. |
| Admin role semantics lost | `get_admin_user`, admin/plugin/webhook/treasury | High | Medium | Map admin to explicit capability entitlement. | Admin policy capability tests. |
| Subscriptions not mapped to entitlements | `UserSubscription`, plan docs/services | High | Medium | Build entitlement migration model before disabling legacy auth. | Entitlement surface/API tests. |
| Bot delegated access over-broad | `app/bot/*` | High | Medium | Child-pass scopes and Telegram binding verification. | Bot policy denied/allowed tests. |

## 14. Legacy Auth Removal Plan

1. **Stage 1: Audit and freeze legacy auth.** Keep runtime behavior unchanged; add documentation and release gate plan.
2. **Stage 2: Add Access Layer models and services beside legacy auth.** Do not remove old auth until parity exists.
3. **Stage 3: Add Access API and Proof-of-Access dependencies.** Implement challenge/session/device/entitlement/revocation/audit-chain flows.
4. **Stage 4: Move protected endpoints to Access dependencies.** Route-by-route policy checks with deny-by-default fallback.
5. **Stage 5: Migrate SDKs and frontend.** Replace bearer helpers with Proof-of-Possession signing and Access import/challenge UX.
6. **Stage 6: Disable `/auth/register` and `/auth/login`.** OpenAPI/docs must mark removed/deprecated; production must not issue bearer tokens.
7. **Stage 7: Remove password/JWT/bearer auth code.** Delete schemas/services/dependencies/config and migrate DB columns/tables.
8. **Stage 8: Add release gate preventing reintroduction.** Static tests fail on password login, bearer Access Pass, JWT auth paths, and frontend token storage.

## 15. Replacement Architecture Map

Future Access Layer file map:

```text
app/domain/access/
app/schemas/access.py
app/db/models/access.py
app/services/access/
app/services/access/crypto/
app/services/access/payments/
app/api/v1/access.py
app/api/access_dependencies.py
tests/security/test_no_password_auth.py
tests/security/test_no_bearer_access_pass.py
tests/integration/test_access_full_flow.py
```

Suggested responsibilities:

- `app/domain/access/`: entitlement, session, device, revocation, policy domain types.
- `app/schemas/access.py`: payment proof, challenge, session, device registration, revocation, audit DTOs.
- `app/db/models/access.py`: access grants, entitlements, device keys, challenges, sessions, revocations, audit-chain records.
- `app/services/access/crypto/`: canonical request, signing verification, body hash, nonce/timestamp validation.
- `app/services/access/payments/`: BTCPay/payment proof ingestion and entitlement issuance.
- `app/api/access_dependencies.py`: Proof-of-Possession and Policy Engine dependencies.

## 16. Acceptance Criteria for This Audit

This audit satisfies the prompt criteria as follows:

- Legacy auth files are listed in Sections 2-6.
- Bearer/JWT/token paths are listed and classified in Section 5.
- SDK auth assumptions are listed in Section 7.
- Frontend auth assumptions are listed in Section 8.
- Protected endpoint dependencies are listed in Section 6.
- Docs/env references are listed in Sections 11-12.
- Tests needing migration are listed in Section 10.
- A clear legacy removal plan exists in Section 14.
- No runtime behavior was changed; only this audit document was added.

## Validation Notes

Validation was run after adding this audit document. Results are intentionally recorded here because this is an audit-only prompt and existing repository state may have unrelated failures.

| Command | Result | Notes |
|---|---|---|
| `pytest` | Warning / repository-state failure | 1143 passed, 3 skipped, 13 failed. Failures are async-test collection/execution failures caused by unknown `pytest.mark.asyncio` / missing native async test support in MCP and SDK async tests, not by this Markdown-only audit. |
| `pytest tests/test_api_contracts.py` | Passed | 2 passed, 2 warnings. |
| `pytest tests/test_openapi_contract.py` | Passed | 1 passed, 6 warnings; warnings include duplicate operation IDs in existing API/web routes. |
| `pytest tests/security/` | Passed | 30 passed, 2 warnings. |
| `ruff check .` | Warning / repository-state failure | 8 existing script lint errors: E402 imports in schema/parity scripts, one unused `sqlalchemy.text`, and E701/E702 one-line statements. |
| `mypy app sdk` | Passed | Success: no issues found in 784 source files. |

## Concise Summary Requested by Prompt

1. Legacy auth files found: **42**.
2. Bearer/JWT/token usage files found: **131**.
3. Frontend auth assumption files found: **13**.
4. SDK auth assumption files found: **17**.
5. Tests impacted: **50**.
6. Top 10 migration risks:
   1. hidden bearer fallback;
   2. password auth accidentally retained;
   3. frontend still showing login/register UX;
   4. SDK still sending `Authorization: Bearer`;
   5. protected endpoint missing Policy Engine;
   6. old `User` model still treated as auth identity;
   7. logs leaking raw Access Pass/session/signature material;
   8. token stored in browser;
   9. migration breaking public endpoints;
   10. OpenAPI still advertising password login.
7. Recommended next prompt: **Prompt 01/33 — Access Layer ADR**.
