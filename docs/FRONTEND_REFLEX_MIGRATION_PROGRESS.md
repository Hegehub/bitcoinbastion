# Frontend Reflex Migration Progress

## Prompt 14/22 — Console Modules: Trace, Evidence, Provider Health, Policy, Audit

### Status

Partial implemented. The Reflex Console core modules now render read-first, advisory, no-custody, non-executing operator surfaces. No backend domain logic, transaction signing, wallet custody, Market migration, Time Machine migration, Sovereign Grid migration, or API Explorer migration was added.

### Routes added or completed

- `/console/trace`
- `/console/evidence`
- `/console/provider-health`
- `/console/policy`
- `/console/audit`

All five routes use the shared Prompt 13 Console dashboard shell and layout.

### Components added

- `components/console/trace_console_panel.py`
- `components/console/evidence_console_panel.py`
- `components/console/provider_health_panel.py`
- `components/console/policy_console_panel.py`
- `components/console/audit_log_panel.py`
- `components/console/degraded_state_banner.py`
- `components/console/module_status_card.py`

### Service clients added

- `services/provider_health_client.py`
- `services/policy_client.py`
- `services/audit_client.py`

Existing `TraceApiClient` and `EvidenceApiClient` remain the report-specific client paths for Trace and Evidence console lookups.

### State modules added

- `state/console_trace_state.py`
- `state/console_evidence_state.py`
- `state/console_provider_health_state.py`
- `state/console_policy_state.py`
- `state/console_audit_state.py`

State defaults are conservative: loading is false, errors are empty, degraded is true for incomplete baseline views, and provider health is `unknown` unless backend data proves otherwise.

### Backend endpoints used

- `/api/v1/public/trace/{report_id}/summary`
- `/api/v1/trace/report/{report_id}`
- `/api/v1/trace/report/{report_id}/evidence`
- `/api/v1/trace/report/{report_id}/provider-disagreement`
- `/api/v1/trace/report/{report_id}/policy-facts`
- `/api/v1/health`
- `/api/v1/observability`

### Backend endpoints missing or not yet stable

- `GET /api/v1/trace/recent` for recent Trace reports.
- `GET /api/v1/evidence` for a global evidence packet listing.
- `GET /api/v1/provider-health` for global provider/source health matrix data.
- `GET /api/v1/policy` for global policy rule/evaluation summaries.
- `GET /api/v1/audit/events` for frontend-facing audit event listing.

The UI labels these as baseline or placeholder areas and does not fabricate production rows.

### Placeholder and baseline areas

- Recent Trace reports are a baseline placeholder until a recent-reports endpoint exists.
- Evidence Console does not fabricate packet listings and points operators to report-specific evidence endpoints.
- Provider Health shows `unknown` rather than pretending providers are healthy.
- Policy Console is read-only and does not expose execution actions.
- Audit Console does not claim immutable/WORM audit storage exists.

### Safety constraints verified

- No seed phrase input.
- No private key input.
- No xprv/yprv/zprv input.
- No wallet file upload.
- No keystore upload.
- No signing-material input.
- No transaction signing.
- No custody.
- No auto-execution.
- No legal-verdict, Bitcoin-consensus-proof, or financial-advice UI.
- Forbidden user-facing wording is covered by tests.

### Tests added

- `reflex_frontend/tests/test_console_core_modules.py`
- `reflex_frontend/tests/test_console_safety.py`
- `reflex_frontend/tests/test_console_api_clients.py`
- `reflex_frontend/tests/test_console_navigation.py`

### Known blockers

- Backend recent Trace report listing is missing.
- Backend global Evidence listing is missing or not stabilized for Reflex.
- Backend global Provider Health endpoint is missing.
- Backend global Policy summary endpoint is missing.
- Backend global Audit events endpoint and immutable audit storage are not implemented in this prompt.
- Full Console module internals continue in later prompts.
