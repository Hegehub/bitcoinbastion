# Endpoint Disposition Register

Generated at `2026-08-08T18:18:59+00:00` from `d9aa4b8f1840fd799a3b44f4403c83544b881a51`. Each runtime operation/channel occurs once in the machine matrix.

## Totals

- **CALLBACK_ONLY:** 18
- **DEFERRED_WITH_REASON:** 4
- **PROTOCOL_ONLY:** 25
- **SEPARATE_PRODUCT:** 13
- **UI_OPTIONAL:** 55
- **UI_REQUIRED:** 263

## Rules

- Callback and protocol receivers remain backend-owned; operator workflows may use separate read models.
- PayRegister remains a separate feature-flagged product and is not core navigation.
- UI mutations remain ineligible until authorization, Human Intent, idempotency, audit, confirmation, error and rollback are proven.
- `NOT_STARTED` is deliberately conservative: source presence is not request-to-render evidence.

See `00_openapi_frontend_rendering_matrix.json` for complete records and reasons.
