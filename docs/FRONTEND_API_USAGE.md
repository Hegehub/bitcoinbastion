# Frontend API Usage

Frontend uses presentation-safe APIs:
- `/api/v1/public/*`
- Trace presentation endpoint for report summary.

No transaction signing and no seed/private key handling in frontend.


Type and transport strategy: Reflex clients under
`frontend/bastion_ui/services/` use Python DTOs and shared envelope/error
handling. Automated client generation from OpenAPI remains pending.

## Access frontend API usage

The frontend Access flow is checkout/import/session based, not login/register based. The UI should create Access payment intents, wait for payment settlement, issue/show the Bastion Access Pass once, import the pass into a challenge flow, create a short-lived PoP session, and then call protected APIs with `X-Bastion-*` headers. Frontends must not store raw Access Passes, recovery phrases, Bitcoin seeds, private keys, or raw signatures in localStorage or analytics.

## Wallet-first and LNURL API usage

The primary Reflex frontend now uses centralized `WalletAuthApiClient`, `LnurlApiClient`, and `PopApiClient` adapters. Wallet endpoints use `/api/v1/wallet-auth/*`; the LNURL router is mounted at `/v1/lnurl/*`. PoP requests use the production `Authorization: PoP`, `Bastion-Request-Timestamp`, `Bastion-Request-Nonce`, `Bastion-Request-Body-Hash`, `Bastion-Request-Signature`, and `Bastion-Principal` headers with backend/Python-compatible canonicalization. Every request receives a new cryptographic nonce and signature.

The frontend does not verify BIP-322 or LNURL signatures. It submits public external-wallet proof and treats principal creation, Device Binding, session issuance, policy, revocation, settlement, and entitlement activation as backend decisions. The LNURL router currently exposes no auth-attempt status endpoint and no withdraw-status endpoint, so the frontend shows those flows as unavailable rather than simulating polling or completion.

LNURL-pay activation requires `settled=true` and a backend entitlement reference. Invoice issuance, QR scanning, comments, payerData, and wallet UI success never activate access. successAction URLs are displayed only after backend verification and require deliberate allowlisted/same-origin navigation.
