# Frontend API Usage

Frontend uses presentation-safe APIs:
- `/api/v1/public/*`
- Trace presentation endpoint for report summary.

No transaction signing and no seed/private key handling in frontend.


Type and transport strategy: Reflex clients under
`reflex_frontend/bastion_ui/services/` use Python DTOs and shared envelope/error
handling. Automated client generation from OpenAPI remains pending.

## Access frontend API usage

The frontend Access flow is checkout/import/session based, not login/register based. The UI should create Access payment intents, wait for payment settlement, issue/show the Bastion Access Pass once, import the pass into a challenge flow, create a short-lived PoP session, and then call protected APIs with `X-Bastion-*` headers. Frontends must not store raw Access Passes, recovery phrases, Bitcoin seeds, private keys, or raw signatures in localStorage or analytics.
