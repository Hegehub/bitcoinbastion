# Endpoint Disposition Register

Generated at `2026-08-09T17:08:21+00:00` from `298a34dc1c12e97d458e56f1a80e0c40482cbc3d`. Each runtime operation/channel occurs once in the machine matrix.

## Totals

- **CALLBACK_ONLY:** 18
- **DEFERRED_WITH_REASON:** 119
- **PROTOCOL_ONLY:** 25
- **SEPARATE_PRODUCT:** 13
- **UI_OPTIONAL:** 1
- **UI_REQUIRED:** 202

## Rules

- Callback and protocol receivers remain backend-owned; operator workflows may use separate read models.
- PayRegister remains a separate feature-flagged product and is not core navigation.
- UI mutations remain ineligible until authorization, Human Intent, idempotency, audit, confirmation, error and rollback are proven.
- `NOT_STARTED` is deliberately conservative: source presence is not request-to-render evidence.

See `00_openapi_frontend_rendering_matrix.json` for complete records and reasons.
