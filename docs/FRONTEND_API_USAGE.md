# Frontend API Usage

Frontend uses presentation-safe APIs:
- `/api/v1/public/*`
- Trace presentation endpoint for report summary.

No transaction signing and no seed/private key handling in frontend.


Type strategy: `frontend/types/api.ts` and `frontend/services/apiClient.ts` provide manual synchronized baseline contracts. Automated `generate:api-types` is pending.
