# Endpoint Disposition Register

Generated at `2026-08-10T16:11:31+00:00` from `818acbe761a20b84940ba9493076c09a78bbc22e`. Each runtime operation/channel occurs once in the machine matrix.

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
