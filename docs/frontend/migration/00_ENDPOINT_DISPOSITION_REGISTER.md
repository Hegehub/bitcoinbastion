# Endpoint Disposition Register

Generated at `2026-08-08T16:32:55+00:00` from `08f6ed2b2fe8a14693e86b2427dc482085a873e4`. Each runtime operation/channel occurs once in the machine matrix.

## Totals

- **CALLBACK_ONLY:** 18
- **PROTOCOL_ONLY:** 25
- **SEPARATE_PRODUCT:** 13
- **UI_OPTIONAL:** 58
- **UI_REQUIRED:** 264

## Rules

- Callback and protocol receivers remain backend-owned; operator workflows may use separate read models.
- PayRegister remains a separate feature-flagged product and is not core navigation.
- UI mutations remain ineligible until authorization, Human Intent, idempotency, audit, confirmation, error and rollback are proven.
- `NOT_STARTED` is deliberately conservative: source presence is not request-to-render evidence.

See `00_openapi_frontend_rendering_matrix.json` for complete records and reasons.
