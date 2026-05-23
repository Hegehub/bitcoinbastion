# Bastion Trace API

This document lists Bastion Trace routes implemented in `app/api/v1/trace.py`.

## Conventions
- Prefix: `/api/v1/trace`
- Envelope: `ResponseEnvelope[T]`
- Safety: advisory-only, no-custody, no signing/broadcast

## Core analysis
- `GET /address/{address}` — analyze public Bitcoin address (BASELINE/IMPLEMENTED)
- `GET /report/{report_id}` — fetch persisted report summary (IMPLEMENTED)
- `GET /report/{report_id}/evidence` — evidence rows for report (IMPLEMENTED)

## Source/watchlist/origin
- `GET /sources` (IMPLEMENTED)
- `GET /sources/{source_name}` (IMPLEMENTED)
- `GET /watchlist` (IMPLEMENTED)
- `POST /watchlist` (IMPLEMENTED)
- `GET /report/{report_id}/origin-passport` (IMPLEMENTED)
- `GET /report/{report_id}/source-summary` (IMPLEMENTED)
- `GET /report/{report_id}/provider-disagreement` (IMPLEMENTED)

## Privacy shield
- `GET /report/{report_id}/privacy-shield` (IMPLEMENTED)
- `GET /report/{report_id}/utxo-hygiene` (IMPLEMENTED)
- `GET /report/{report_id}/dust-radar` (IMPLEMENTED)

## Counterparty/payment context
- `GET /report/{report_id}/counterparty-lens` (IMPLEMENTED)
- `POST /payment-context` (BASELINE/IMPLEMENTED)
- `POST /payment-intent/preview` (BASELINE/IMPLEMENTED)
- `POST /destination-review` (BASELINE/IMPLEMENTED)

## Lite
- `GET /lite/{address}` (IMPLEMENTED)

## Business/enterprise/platform integration
- `GET /business/profile` (BASELINE/IMPLEMENTED)
- `POST /business/batch` (BASELINE/IMPLEMENTED)
- `GET /business/policy-profiles` (BASELINE/IMPLEMENTED)
- `GET /business/events` (BASELINE/IMPLEMENTED)
- `GET /enterprise/profile` (BASELINE/IMPLEMENTED)
- `GET /enterprise/rbac/roles` (PLACEHOLDER/IMPLEMENTED)
- `GET /enterprise/rbac/permissions` (PLACEHOLDER/IMPLEMENTED)
- `GET /enterprise/rbac/default-policy` (PLACEHOLDER/IMPLEMENTED)
- `GET /enterprise/sso` (PLACEHOLDER/IMPLEMENTED)
- `POST /enterprise/evidence-access/evaluate` (BASELINE/IMPLEMENTED)
- `POST /enterprise/proof-packet` (BASELINE/IMPLEMENTED)

## Integration bridge routes
- `GET /report/{report_id}/citadel-contribution` (BASELINE/IMPLEMENTED)
- `GET /report/{report_id}/policy-facts` (BASELINE/IMPLEMENTED)
- `POST /treasury/destination-check` (BASELINE/IMPLEMENTED)
- `POST /register/payment-advisory` (BASELINE/IMPLEMENTED)
- `GET /report/{report_id}/evidence-refs` (BASELINE/IMPLEMENTED)

## Observability/runtime
- `GET /status` (IMPLEMENTED)
- `GET /events` (IMPLEMENTED)
- `GET /events/{event_id}` (IMPLEMENTED)
- `GET /alerts` (BASELINE/IMPLEMENTED)

## Not currently implemented in this router
- `POST /lite/check`
- `GET /report/{report_id}/timeline`
- `GET /report/{report_id}/receipt`
- `POST /report/{report_id}/replay`
- `POST /report/{report_id}/proof-packet`
- `GET /report/{report_id}/proof-packet`

## Error cases (current behavior)
- `400` invalid Bitcoin address/sensitive wallet material.
- `404` report/event/source not found.
- Placeholder/baseline features return advisory or limited outputs; do not imply production enforcement.
