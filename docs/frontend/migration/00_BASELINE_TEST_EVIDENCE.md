# Baseline Test Evidence — Prompt 0/25

Revision: `63538ae5788b1df924f1aa459e500891011ed83a`; branch `work`; Linux container; Python 3.12.13; default application configuration. Proxy variables were explicitly removed only for Python frontend/test commands to reproduce the repository's isolated test profile; application configuration was not changed. Durations are observed wall-time approximations. Mocked/unavailable checks are never PASS.

| Gate | Exact command | Evidence class | Result | Duration / notes |
|---|---|---|---|---|
| Runtime OpenAPI/WS generation and diff | `python scripts/generate_frontend_migration_audit.py` | runtime-generated/local | PASS | ~13s; 351/369 HTTP, 9 WS, six security schemes; four FastAPI warnings and one duplicate final ID |
| Duplicate/disposition/feature/prompt integrity | `python scripts/validate_frontend_migration_baseline.py` | contract-generated/local | PASS | 369 HTTP + 9 WS unique records; 69 IDs; 53 old prompt IDs |
| URL/client-path inventory | generation command above (`00_FRONTEND_URL_AUDIT.json`) | source inventory | PASS | 68 literals; 53 matched, 15 stale/absent (inventory pass, not parity) |
| Route/workflow/transformation inventory | `rg` counts recorded in baseline and matrices | source inventory | PASS | deterministic declarations only; ownership/unsafe semantics remain UNAVAILABLE |
| Frontend Ruff | `cd frontend && env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY uv run ruff check bastion_ui` | executed local | PASS | all checks passed |
| Frontend mypy | `cd frontend && env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY uv run mypy bastion_ui` | executed local | PASS | 354 files |
| Frontend pytest | `cd frontend && env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY uv run pytest` | executed local/mocked tests | PASS | 147 passed in 3.50s |
| Root API/contract/security | `env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY pytest -q tests/contract/test_access_openapi_contract.py tests/contract/test_websocket_contract.py tests/contract/test_websocket_streams.py tests/security/test_access_certificate_not_bearer.py tests/security/test_human_intent_required.py tests/security/test_entitlement_not_bearer_access.py` | executed contract/security | PASS | 45 passed in 14.36s; five warnings |
| Existing parity checker | `python scripts/check_route_api_parity.py` | static/source-string | PASS | non-authoritative and insufficient alone; it labels registration/source presence implemented |
| Documentation status/link truth | `python scripts/check_docs_truthfulness.py` | static documentation | PASS | routes=294, models=161; index links added; old plan explicitly superseded |
| Reflex export | `cd frontend && env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY uv run reflex export --no-zip` | executed build/export | PASS | compiled 148/147; warnings for implicit sitemap plugin, old Reflex/Node and deprecated theme API |
| Browser startup/route smoke | no deterministic browser command exists at HEAD | browser | BLOCKED | export is not browser evidence |
| Desktop/mobile/keyboard/adaptive modes | no deterministic browser command exists at HEAD | browser | BLOCKED | 1440×900, 430×932, keyboard, reduced motion/transparency, high contrast unverified |
| Forced status/degraded harness | no deterministic interception harness exists at HEAD | browser | BLOCKED | offline/degraded/401/403/404/409/422/429/5xx unverified |
| CI/production | not invoked | CI/production | NOT RUN | local Prompt-0 evidence cannot substitute for immutable CI or production evidence |

No perceptible runnable UI change was made, so a screenshot is not applicable. The duplicate operation ID and stale URL findings are pre-existing contract/frontend debt, not Prompt-0 regressions.

## Prompt 1 prerequisite revalidation

Prompt 1 reran the runtime generator against starting HEAD `08f6ed2b2fe8a14693e86b2427dc482085a873e4` and made timestamp metadata deterministic. Contract counts remained unchanged. The prompt stopped before Feature 53 because of the exact blockers in `01_CONTRACT_FOUNDATION_BLOCKERS.md`; no coverage promotion occurred.
