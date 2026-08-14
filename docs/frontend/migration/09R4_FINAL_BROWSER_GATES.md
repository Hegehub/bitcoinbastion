# Prompt 9R4 final browser gates

## Two-blocker evidence

| Blocker | Existing implementation | Exact failure | Required fix | Browser proof |
|---|---|---|---|---|
| Device-bound PoP browser authority | Backend `AccessSession`/certificate/device verifier and frontend signing primitives existed, but `HttpTransport` had no signer injection boundary | Every protected generated operation failed closed before making a request | Inject a process-local request-security provider; provision an ephemeral least-privilege session only in the integration runner | Chromium loads `/operations/jobs`, the real API accepts a fresh signed request, and named job fields render with `LIVE` provenance |
| Command-palette keyboard activation | The trigger used an `accesskey`, while key handling existed only inside the open palette input | A real `/` keypress had no mounted global owner and could not open the palette | Mount one idempotent global `/` listener in the application shell and delegate to the canonical trigger | Chromium `/` opens the named dialog, focuses search, and keyboard-only search/activation navigates canonical routes |

## Security inventory and isolation

`app/api/access_dependencies.py` and `AccessRequestVerifier` are the production path. The
Access database models and Ed25519 signing suite are canonical reusable infrastructure.
`tests/helpers/access.py` uses dependency overrides and is therefore unit/integration-only;
it is deliberately not used for this browser proof. The browser support package is loaded
only through an explicit test-process `PYTHONPATH` and environment opt-in. There is no test
HTTP endpoint, query parameter, production default, stored browser state, static token, or
committed private key.

The runner creates an ephemeral Ed25519 key, active certificate/device/session, and
`business_pass` entitlement restricted to `operations:read`. Every protected request uses a
fresh timestamp and nonce and is signed over the canonical method/path/query/body digest.
The normal verifier checks token hash, expiry, device fingerprint, signature, and replay
nonce. The database, key material, processes, and session disappear during runner cleanup.

## Jobs request-to-render lineage

`GET /api/v1/operations/jobs` → `BackgroundJobHealthOut.job_name`, `health_state`,
`last_start_at`, `last_finish_at`, `next_scheduled_at`, and bounded `failure_reason` →
`adapt_jobs` → `JobViewModel` → `JobsState.value` → `jobs_screen` → `.job-name`,
`.job-status`, timing text, and `.job-failure`. The integration record is seeded through the
backend database model, retrieved through the real protected operation, and is not a
Feature-60 fixture. Worker identity, token, proof, and private key are excluded from DOM.

## Command ownership and behavior

The sole owner is `global_command_shortcut()` mounted once by `app_shell()`. It removes a
previous handler before mounting, ignores modified keystrokes and editable controls, and
delegates to the visible canonical trigger. The documented `/` shortcut is unchanged.
Palette roles remain dialog/listbox/option, autofocus targets the search input, Escape uses
the existing focus-return event, and route commands continue to be resolved by the canonical
route/flag/security registry. Market Signals is now a discoverable Prompt-9 route command.

## Rollback

Remove the shell script mount and signer-provider injection boundary, then delete
`tests/browser_support`. This restores fail-closed protected transport and the previous
click-only palette without changing Feature 67, backend Access, Jobs contracts, Market
semantics, Incident/SLO authority, or persisted user data.
