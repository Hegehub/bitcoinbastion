# Baseline Test Evidence

Revision: `ee2792fe4397184f9d6f068b7cee7c2b19fe17e8`; environment: Linux container, Python 3.12, current default runtime profile. Results below are updated only from actual commands; skipped/mocked/unavailable is never PASS.

| Gate | Exact command | Result | Duration / notes |
|---|---|---|---|
| Snapshot + duplicate IDs | `time python scripts/generate_frontend_migration_audit.py` | PASS with contract warning | ~10s; one duplicate final operation ID; 9 WS registrations |
| Frontend Ruff | `cd frontend && uv run ruff check .` | PASS | 13.3s |
| Frontend mypy | `cd frontend && uv run mypy bastion_ui` | PASS | 4.5s; 354 files |
| Frontend pytest | `cd frontend && uv run pytest` | PASS | 21.7s; 147 passed |
| Root contract/security | `pytest -q tests/security/test_no_bitcoin_seed_auth.py tests/security/test_legacy_auth_disabled.py tests/security/test_wallet_auth_api_security.py tests/security/test_access_sensitive_logging.py` | PASS | 11.8s; 23 passed, 5 warnings |
| Existing parity | `python scripts/check_route_api_parity.py` | PASS | 4.2s; non-authoritative static checker overclaims implementation |
| Matrix validator | `python scripts/generate_frontend_migration_audit.py` | PASS | generation includes exactly-once stable IDs and deterministic order |
| Reflex export | `cd frontend && uv run reflex export --frontend-only --no-zip` | PASS | ~36s; warnings for Node version, Reflex version and deprecated theme API |
| Browser/startup/screens/a11y/forced states | browser harness | BLOCKED | no deterministic Prompt-0 browser interception/evidence harness established |
| Docker | `docker version` | BLOCKED | Docker executable unavailable |

Browser gates individually remain **BLOCKED**, not passed: startup, 1440×900, 430×932, keyboard-only, reduced motion, reduced transparency, forced offline/degraded/401/403/404/409/422/429/5xx. Prompt 0 makes no perceptible UI change, so no change screenshot is required.
