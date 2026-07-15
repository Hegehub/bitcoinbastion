# Access Layer Release Gate

This gate is the final cleanup guard for the Bastion Proof-of-Access migration. It must pass before a release can claim that protected API access no longer depends on legacy email, username, password, JWT, bearer-token, or raw Access Pass authentication.

The gate is intentionally a release-readiness guard, not a runtime feature. It must not weaken Proof-of-Access behavior, add bearer fallback, or fake production readiness.

## How to run locally

```bash
make access-release-gate
```

The target runs focused security, Access OpenAPI contract, Access full-flow integration, Python SDK, and TypeScript SDK checks. It is the local equivalent of the Access release gate job.

## Exact checks

The release gate fails if any of the following are true:

1. **Legacy password auth is active**
   - `/auth/register` creates a password account.
   - `/auth/login` issues an access token or bearer/JWT token.
   - `LoginRequest`, `RegisterRequest`, or `TokenResponse` are advertised as active production auth schemas.
   - password hashing or username/password tests can authenticate to a protected API.

2. **Access Pass behaves like a bearer token**
   - `Authorization: Bearer <access_pass>` grants access.
   - a raw Bastion Access Pass alone grants access.
   - protected endpoints accept a raw pass without device proof, session, and policy.
   - SDK docs/examples encourage bearer-pass usage.

3. **Protected endpoints bypass Proof-of-Access dependencies**
   - business, enterprise, treasury, policy management, metrics, API-key management, webhook management, private dashboard, operator/admin, PayRegister-private, or Trace business/enterprise endpoints skip Access dependencies.
   - protected endpoints must use the final equivalent of `require_access_session`, `require_scope`, `require_plan`, `require_metric_entitlement`, `require_policy_decision`, or step-up/human-intent dependencies.

4. **Policy Engine is bypassed**
   - protected requests only check that a session, token, plan string, or API key exists.
   - protected requests cannot produce structured policy decisions such as `allow`, `deny`, `upgrade_required`, `step_up_required`, `quota_exceeded`, `metric_not_allowed`, `revoked`, `expired`, `recovery_required`, or `online_check_required`.

5. **Payment proof does not gate issuance**
   - Access Certificates or Subscription Entitlements can be issued before verified payment settlement.
   - manual grants work in production without explicit `ACCESS_ALLOW_MANUAL_GRANTS=true`.
   - duplicate webhooks issue duplicate certificates.
   - unpaid or expired invoices create entitlements.

6. **Full Access flow regresses**
   - payment intent → paid/test settlement → certificate → entitlement → origin-bound challenge → challenge verification → PoP session → protected access → audit coverage fails.

7. **Replay protection regresses**
   - reused nonces, reused challenges, expired challenges, stale timestamps, body tampering, path/method tampering, or invalid signatures are accepted.

8. **Revocation and lockdown regress**
   - revoked pass/device/session/child API key/delegated pass remains usable.
   - lockdown does not freeze active sessions.
   - entitlement downgrades do not freeze invalid permissions.

9. **Recovery becomes unsafe**
   - recovery accepts Bitcoin seed/private-key material.
   - raw recovery phrases are stored or logged.
   - Pro/Business/Enterprise recovery completes with a single weak factor.
   - support-only recovery exists.
   - recovery is easier than login/session creation or lacks audit coverage.

10. **Sensitive redaction regresses**
    - logs, tests, docs, audit events, or examples expose raw Access Passes, raw session tokens, raw recovery phrases, raw private keys, raw issuer keys, BTCPay API keys, `ACCESS_SERVER_PEPPER`, `ACCESS_ISSUER_PRIVATE_KEY`, device private keys, or Bitcoin seed/private-key material.

11. **OpenAPI contract regresses**
    - OpenAPI advertises active password login, password registration, bearer login token issuance, mandatory email account creation, unrestricted API key access, or endpoints bypassing Proof-of-Access.
    - OpenAPI must document Access payment intent, certificate, challenge, session, entitlement, recovery, lockdown, and metric endpoints when implemented.

12. **SDKs regress to bearer auth**
    - Python or TypeScript SDK protected calls require or emit legacy bearer auth.
    - SDK examples encourage `Authorization: Bearer <access_pass>`, password login, raw pass logging, or raw recovery phrase storage.
    - SDKs must support `X-Bastion-Session`, `X-Bastion-Timestamp`, `X-Bastion-Nonce`, `X-Bastion-Body-Hash`, and `X-Bastion-Signature`.

13. **Frontend/reflex login returns**
    - active password login/register/reset forms, mandatory email signup, browser-only critical approval, or Bitcoin seed input returns.
    - optional contact binding and clearly-deprecated migration docs are allowed.

14. **Environment config regresses**
    - production config requires `JWT_SECRET_KEY`, password hash secrets, mandatory email auth, or legacy auth enablement for primary protected API access.
    - `.env.example` must include safe placeholders for `ACCESS_SERVER_PEPPER`, `ACCESS_ISSUER_KEY_ID`, `ACCESS_ISSUER_PRIVATE_KEY`, `ACCESS_SESSION_TTL_SECONDS`, `ACCESS_CHALLENGE_TTL_SECONDS`, `ACCESS_ALLOW_MANUAL_GRANTS=false`, and BTCPay settings.

## Allowed public endpoints

The following categories may remain public without Proof-of-Access if their responses contain no private/premium data:

- `health/live` and safe readiness endpoints;
- public site, roadmap, feature catalog, landing, and static docs APIs;
- public non-sensitive status endpoints;
- Trace Lite/public address checks when intentionally public;
- OpenAPI/docs endpoints.

## Forbidden legacy auth patterns

The following patterns are forbidden in active protected authentication paths:

- username/password login;
- email/password registration;
- password reset as recovery for protected API access;
- JWT bearer access for protected APIs;
- raw Access Pass as bearer proof;
- support-only recovery;
- Bitcoin wallet seed/private-key authentication;
- SDK or frontend examples teaching `Authorization: Bearer <access_pass>`.

## How to interpret failures

- A gate failure in `tests/security/` means a security invariant regressed and must block release.
- A failure in `tests/contract/test_access_openapi_contract.py` means the public API contract no longer truthfully describes Proof-of-Access.
- A failure in `tests/integration/test_access_full_flow.py` means the Access lifecycle is not release-ready.
- SDK test failures mean clients may regress to legacy bearer assumptions or fail to sign protected requests.
- Full-suite failures outside the Access gate must be triaged separately, but they do not permit bypassing this gate.

## Rollback policy

If this gate fails on a release branch, do not ship compatibility fallbacks. Roll back to the last commit where the gate passed, preserve audit evidence, and fix the regression behind Proof-of-Access semantics. Never re-enable password/JWT/bearer auth as a rollback shortcut.

## Emergency exception policy

Emergency exceptions require a written security-owner approval, a linked incident, a bounded time limit, and a compensating control. Exceptions may not allow Bitcoin seed/private-key auth, raw Access Pass bearer auth, or support-only recovery.

## Future PQ-readiness note

Bastion may keep crypto-agility metadata and future ML-KEM/ML-DSA/SLH-DSA placeholders. The gate must fail any documentation or test claim that post-quantum cryptography is production-implemented unless real implementations and test vectors exist.

## Safe remaining references

The repository may still contain the words `password`, `bearer`, `JWT`, `Authorization`, or `access_token` only in these safe contexts:

- disabled legacy endpoint responses and fail-closed compatibility shims;
- tests that assert legacy auth is rejected;
- documentation explaining the migration away from legacy auth;
- non-auth infrastructure secrets such as database or ClickHouse passwords;
- security redaction deny-lists;
- bot/service bearer tokens that are not user protected-API authentication.

## Required verification commands

```bash
make access-release-gate
pytest tests/security/
pytest tests/contract/test_access_openapi_contract.py
pytest tests/integration/test_access_full_flow.py
pytest tests/test_openapi_contract.py tests/test_api_contracts.py
pytest sdk/python/tests/
cd sdk/typescript && npm test
```

Release evidence must include classification of remaining legacy-auth text matches. No active protected endpoint may rely on email, username, password, JWT bearer, or a raw Access Pass.

## Validation notes

As of 2026-07-07, the focused Access gate passes locally. Known repository-wide issues that must not be hidden:

- `pytest tests/contract/ -q` has older non-Access contract tests that still override legacy `get_admin_user` or expect unauthenticated protected endpoint behavior; targeted Access OpenAPI contract tests pass.
- `ruff check .` reports pre-existing lint issues in `scripts/` unrelated to Access Layer release-gate logic.

## 2026-07-07 cleanup search snapshot

Repository-wide search after Prompt 32 cleanup found remaining legacy-auth terms only in safe buckets above. Counts from `rg -l` over `app`, `sdk`, `docs`, `tests`, `frontend`, and `.env.example` were:

| Term | Files with remaining references | Classification |
| --- | ---: | --- |
| `password` | 67 | disabled legacy docs/tests, non-auth infrastructure passwords, redaction deny-lists |
| `bearer` | 94 | disabled legacy docs/tests, storage safety rules, bot service bearer setting, redaction deny-lists |
| `JWT` | 21 | disabled legacy env/docs/tests only |
| `access_token` | 15 | tests/redaction/storage safety and disabled legacy assertions |
| `LoginRequest` | 6 | disabled compatibility schema/tests only |
| `RegisterRequest` | 6 | disabled compatibility schema/tests only |
| `TokenResponse` | 5 | disabled compatibility schema/tests only |
| `get_current_user` | 4 | fail-closed dependency shim and tests only |
| `Authorization` | 31 | docs/tests rejecting bearer semantics or non-auth safety references |

Any future increase in these counts must be reviewed before release; any active protected API path using these terms for authentication must fail this gate.
