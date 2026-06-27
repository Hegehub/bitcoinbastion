# Reflex Frontend Migration Status

## Prompt 15/22 — Advanced Console Modules

Status: partial implemented. Frontend shell complete, backend data source pending for several advanced module panels.

### Implemented advanced console routes

- `/console/market-intelligence`
- `/console/time-machine`
- `/console/sovereign-grid`
- `/console/api-explorer`

### Backend endpoints used

- `/web/market-time-machine`
- `/web/timeline`
- `/web/candle/{candle_id}`
- `/web/evidence/{packet_id}`
- `/api/v1/public/status`
- `/api/v1/public/roadmap`
- `/api/v1/public/features`
- `/api/v1/signals/top`
- `/api/v1/public/trace/{report_id}/summary`
- `/api/v1/health`
- `/api/v1/observability`

### Backend endpoints missing or pending

- Stable Market Intelligence summary endpoint for console cards.
- Sanitized Sovereign Grid readiness/runtime profile endpoint.
- Global provider freshness endpoint for advanced modules.
- Safe OpenAPI/category metadata endpoint for API Explorer.
- Try-request support for templated endpoints requiring user-provided ids.

### Placeholder and degraded states

- Market Intelligence displays unavailable/latest-signal placeholders until backend DTO data is returned.
- Time Machine displays empty and degraded states instead of fabricated timeline, candle, evidence, or narrative rows.
- Sovereign Grid shows checklist/readiness cards and does not claim mesh, mining, node-wallet, or cluster capability.
- API Explorer marks only safe read examples as tryable and labels all other examples as inspection-only, draft-only, approval-required, or admin-only.

### Safety limitations

- Market Intelligence is advisory-only and not financial advice.
- Market Time Machine states historical similarity is not prediction.
- Sovereign Grid is a frontend readiness view only.
- API Explorer is inspection/read-only focused and warns against wallet-secret material.
- No custody, transaction signing, trading execution, treasury approval, or sensitive input collection was added.

### Tests added

- `reflex_frontend/bastion_ui/tests/test_console_advanced_routes.py`
- `reflex_frontend/bastion_ui/tests/test_console_market_intelligence.py`
- `reflex_frontend/bastion_ui/tests/test_console_time_machine.py`
- `reflex_frontend/bastion_ui/tests/test_console_sovereign_grid.py`
- `reflex_frontend/bastion_ui/tests/test_console_api_explorer.py`
- `reflex_frontend/bastion_ui/tests/test_console_advanced_safety.py`

### Verification

- `cd reflex_frontend && uv run ruff check .` passed.
- `cd reflex_frontend && uv run mypy bastion_ui` passed.
- `cd reflex_frontend && uv run pytest` passed with 90 tests.
- `cd reflex_frontend && uv run reflex export` passed; Reflex emitted existing sitemap/theme and Node-version warnings.
- Repository root `python -m pytest -q` still fails with known baseline async-plugin failures and a pre-existing route-contract assertion unrelated to Prompt 15. Latest run: 14 failed, 868 passed, 2 skipped.
