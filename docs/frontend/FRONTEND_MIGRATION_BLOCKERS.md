# Frontend Migration Blockers

Date: 2026-06-19  
Scope: Next.js legacy freeze, Reflex readiness blockers, Market/Jinja ownership, API parity, safety/no-custody posture.

## Critical

### Trace parity remains a cutover blocker

- Severity: Critical
- Affected area: Trace public routes and Trace API clients
- Current evidence/path: `frontend/app/check/page.tsx`, `frontend/app/trace/page.tsx`, `frontend/app/trace/[reportId]/page.tsx`, `frontend/app/trace/[reportId]/proof-packet/page.tsx`, `frontend/services/apiClient.ts`, `app/api/v1/trace.py`, `app/api/v1/public.py`
- Recommended fixing prompt: Prompt 8/22 and Prompt 9/22
- Notes: Reflex must prove `/check`, `/trace`, `/trace/[report_id]`, and `/trace/[report_id]/proof-packet` before cutover. Next.js remains rollback until then.

### Proof Packet route parity must be proven

- Severity: Critical
- Affected area: Proof Packet page and backend endpoint
- Current evidence/path: `frontend/app/trace/[reportId]/proof-packet/page.tsx`; backend `app/api/v1/trace.py` implements `/api/v1/trace/report/{report_id}/proof-packet`
- Recommended fixing prompt: Prompt 10/22
- Notes: Current backend exists, but Reflex must preserve integrity/redaction/advisory limitation display and unavailable states.

### Reflex cutover attempted before parity

- Severity: Critical
- Affected area: release/cutover process
- Current evidence/path: `docs/FRONTEND_REFLEX_MIGRATION_BASELINE.md`; `frontend/LEGACY_STATUS.md`; this freeze document set
- Recommended fixing prompt: Prompt 22/22 only after prompts 2/22-21/22 pass
- Notes: No production route switch is allowed from this prompt.

### Sensitive material must never be accepted as frontend input

- Severity: Critical
- Affected area: Trace address form, command palette report-id input, future Reflex inputs
- Current evidence/path: `frontend/components/trace/AddressCheckForm.tsx`, `frontend/lib/addressValidation.ts`, `frontend/components/interactive/BastionCommandPalette.tsx`
- Recommended fixing prompt: Prompt 3/22 and Prompt 8/22
- Notes: Current address validation rejects obvious sensitive/non-address values. Command palette rejects several sensitive patterns before generating dynamic Trace actions, but Reflex should add explicit 12/24-word phrase-count tests.

## High

### Market route ownership is unclear for Reflex cutover

- Severity: High
- Affected area: Market Intelligence / Market Time Machine
- Current evidence/path: `app/web/routes_market.py`, `app/web/templates/market/*`, command palette links in `frontend/components/interactive/BastionCommandPalette.tsx`
- Recommended fixing prompt: Prompt 14/22 and Prompt 16/22
- Notes: Current `/market/*` pages are FastAPI/Jinja-owned. Reflex must either mirror them or explicitly delegate them before cutover.

### Console route plan differs from current Next.js route plan

- Severity: High
- Affected area: console/dashboard routes
- Current evidence/path: Next.js has `/dashboard/*`; required target uses `/console/*`; inspected `reflex_frontend/bastion_ui/routes/` currently has no page modules beyond `__init__.py`
- Recommended fixing prompt: Prompt 12/22 and Prompt 15/22
- Notes: Add route tests and redirect/delegation policy before cutover.

### Command palette Market entries do not match final console target paths

- Severity: High
- Affected area: command palette/navigation
- Current evidence/path: `frontend/components/interactive/BastionCommandPalette.tsx` links Market Intelligence to `/market` and Time Machine to `/market/time-machine`
- Recommended fixing prompt: Prompt 5/22
- Notes: Reflex command palette must include `/console/market-intelligence`, `/console/time-machine`, `/console/sovereign-grid`, `/console/policy`, and `/console/audit` while preserving/delegating public Market routes.

### Trace backend has available panel endpoints unused by current Next.js client

- Severity: High
- Affected area: Trace report detail parity
- Current evidence/path: `app/api/v1/trace.py` implements `source-summary`, `utxo-hygiene`, and `dust-radar`; `frontend/services/apiClient.ts` does not expose those calls
- Recommended fixing prompt: Prompt 4/22 and Prompt 9/22
- Notes: Reflex should add service methods and fallback panels, or explicitly document why they are not displayed.

### Trace payment flow route shape mismatch

- Severity: High
- Affected area: Trace payment context / payment intent / destination review APIs
- Current evidence/path: Prompt contract expects report-scoped paths, while `app/api/v1/trace.py` exposes `/api/v1/trace/payment-context`, `/api/v1/trace/payment-intent/preview`, and `/api/v1/trace/destination-review`
- Recommended fixing prompt: Prompt 4/22
- Notes: Align frontend contract before Reflex calls these endpoints.

### Market API prefix expectations do not match actual backend prefixes

- Severity: High
- Affected area: Market / intelligence API contracts
- Current evidence/path: requested groups include `/api/v1/market-data/*`, `/api/v1/market-intelligence/*`, and `/api/v1/intelligence-timeline/*`; actual routers use `/api/v1/market`, `/api/v1/news`, and `/api/v1/intelligence/timeline`
- Recommended fixing prompt: Prompt 4/22 and Prompt 13/22
- Notes: Future Reflex clients must use actual paths or add explicit backend compatibility aliases.

## Medium

### Root pytest async-plugin and Reflex scaffold failures

- Severity: Medium
- Affected area: repository test environment and current Reflex scaffold
- Current evidence/path: `python -m pytest -q` reports async tests are not natively supported and current Reflex contract tests expect route/client/safety files that are not present
- Recommended fixing prompt: testing/tooling maintenance prompt and Prompt 2/22
- Notes: Frontend toolchain checks passed; root suite still needs async test environment alignment and Reflex scaffold work.

### Stale legacy route files require archive/redirect decisions

- Severity: Medium
- Affected area: stale Next.js routes
- Current evidence/path: `frontend/app/products/*`, `frontend/app/self-host/*`, `frontend/app/dashboard/*`, plus `/citadel`, `/treasury`, `/register`, `/enterprise`, `/blog`, `/design-system`, and `/genesis`
- Recommended fixing prompt: Prompt 21/22
- Notes: Do not delete during freeze; decide redirects/archive after Reflex parity.

### Missing Reflex route/API parity tests

- Severity: Medium
- Affected area: Reflex test coverage
- Current evidence/path: baseline requires route, navigation, command palette, API client, Trace safety, no-sensitive-input, forbidden-wording, Market, and console tests
- Recommended fixing prompt: Prompt 17/22
- Notes: Existing Reflex tests cover scaffold/theme/safety helpers but do not prove production cutover parity.

### Docs can drift from migration state

- Severity: Medium
- Affected area: README/status/production readiness docs
- Current evidence/path: `README.md`, `docs/STATUS.md`, `docs/PRODUCTION_READINESS.md`, `docs/FRONTEND_REFLEX_MIGRATION_BASELINE.md`
- Recommended fixing prompt: every migration prompt
- Notes: Do not claim Reflex parity or production cutover before evidence exists.

## Low

### Visual polish parity is not defined

- Severity: Low
- Affected area: Reflex visual/UI migration
- Current evidence/path: current Next.js components under `frontend/components/`; Reflex components under `reflex_frontend/bastion_ui/components/`
- Recommended fixing prompt: later UI polish prompt after route/API/safety parity
- Notes: Do not block safety/API cutover work on animation parity unless product explicitly requires it.

### Duplicated safety copy exists across surfaces

- Severity: Low
- Affected area: copy maintenance
- Current evidence/path: safety copy appears in Next.js components, Reflex helpers, docs, and Jinja templates
- Recommended fixing prompt: Prompt 3/22
- Notes: Centralize copy in Reflex while preserving exact required visible warnings.

## No-Custody / Sensitive Input Risks

No obvious frontend sensitive input collection was found during this audit. This is not an exhaustive security certification.

Observed input surfaces:

- `frontend/components/trace/AddressCheckForm.tsx` and `frontend/lib/addressValidation.ts`: accepts a public Bitcoin address and rejects obvious sensitive/non-address values.
- `frontend/components/interactive/BastionCommandPalette.tsx`: accepts page search or numeric Trace report id; rejects several sensitive patterns before generating dynamic Trace actions.
- FastAPI/Jinja Market query params in `app/web/routes_market.py`: filters, ids, pagination, date/window, status, and sort values; no wallet or secret upload fields were found in the inspected route handlers.

Recommended follow-up:

- Add Reflex tests for explicit 12-word and 24-word mnemonic-like phrase rejection in command palette and address inputs.
- Keep warnings visible: never enter seed phrases, private keys, wallet files, keystores, or signing material.

## Forbidden Wording Audit

The blocked phrases were searched across `frontend/`, `app/web/`, `docs/`, and `README.md`. To avoid turning this audit document into user-facing blocked copy, phrase names below are hyphen-normalized.

Findings:

| Normalized phrase | File | Context | Recommended replacement |
|---|---|---|---|
| `clean-address` | `frontend/lib/security.ts`; several `frontend/tests/*` files | Forbidden-wording detector/test fixtures only | Keep as test fixture; do not render in UX |
| `dirty-address` | `frontend/lib/security.ts`; several `frontend/tests/*` files | Forbidden-wording detector/test fixtures only | Keep as test fixture; do not render in UX |
| `criminal-address` | several `frontend/tests/*` files | Test fixture only | Keep as test fixture; use `elevated risk band` in UX |
| `guaranteed-safe` | `frontend/lib/security.ts`; several `frontend/tests/*` files | Forbidden-wording detector/test fixtures only | Keep as test fixture; use `manual review recommended` or `limited evidence` |
| `approved-payment` | `frontend/lib/security.ts`; several `frontend/tests/*` files | Forbidden-wording detector/test fixtures only | Keep as test fixture; use `operator review required` |
| `verified-illicit` | `frontend/tests/command-palette.test.tsx`; `frontend/tests/trace-report-ui.test.tsx` | Test fixture only | Keep as test fixture; use `provider disagreement` or `insufficient evidence` |

No obvious user-facing rendered copy occurrence of these blocked phrases was found during this audit. Do not treat this as exhaustive legal/security certification.
