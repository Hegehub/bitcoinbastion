# Frontend Reflex Trace Report Dynamic Routes

## Routes implemented

- `/trace/[report_id]`
- `/trace/[report_id]/proof-packet`

## Backend endpoints used

- `GET /api/v1/public/trace/{report_id}/summary`
- `GET /api/v1/trace/report/{report_id}`
- `GET /api/v1/trace/report/{report_id}/evidence`
- `GET /api/v1/trace/report/{report_id}/privacy-shield`
- `GET /api/v1/trace/report/{report_id}/origin-passport`
- `GET /api/v1/trace/report/{report_id}/source-summary`
- `GET /api/v1/trace/report/{report_id}/provider-disagreement`
- `GET /api/v1/trace/report/{report_id}/utxo-hygiene`
- `GET /api/v1/trace/report/{report_id}/dust-radar`
- `GET /api/v1/trace/report/{report_id}/counterparty-lens`
- `GET /api/v1/trace/report/{report_id}/policy-facts`
- `GET /api/v1/trace/report/{report_id}/proof-packet`

## Safety model

Trace report pages are advisory-only. They are not legal verification and are not Bitcoin consensus proof. The frontend does not custody funds, request wallet material, or sign transactions.

## Dynamic route safety

Report identifiers are rejected when empty, too long, or containing path traversal, script-like, or dangerous scheme markers.

## Partial and degraded data

Each panel is loaded independently. If one endpoint fails, the report can still show other successful panels while marking the failed panel path as degraded or unavailable.

## Proof packet availability

The proof packet page does not fabricate packets. If the endpoint is unavailable, the UI says so and avoids placeholder hashes or source metadata.

## Remaining blockers

- Confirm exact backend DTO shape for each detailed panel.
- Confirm whether proof packet endpoint is public-safe, enterprise-only, or pending.
- Add browser-level dynamic route tests when the Reflex runtime route model is finalized.
