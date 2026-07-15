# Frontend Proof-of-Access Flow

The active repository frontend is the Reflex UI under `frontend/`. The legacy
Next.js implementation that previously occupied this path is not active; the
Reflex routes below are the production migration target.

## Routes

- `/access` — plan selection for `lite_pass`, `basic_pass`, `plus_pass`, `pro_pass`, `business_pass`, and `enterprise_pass`.
- `/access/checkout` — creates and polls Access payment intents.
- `/access/success` — issues certificate material only after payment settlement and shows the Bastion Access Pass once.
- `/access/import` — imports a Bastion Access Pass or certificate payload, creates an origin-bound challenge, and starts a Proof-of-Possession session.
- `/access/me` — displays safe plan, scope, entitlement, quota, recovery, revocation, and session metadata.
- `/access/recovery` — explains recovery profiles and calls backend recovery endpoints when available.
- `/access/lockdown` — starts Emergency Lockdown through the backend after policy and Human Intent checks.

## Flow

1. User selects a plan on `/access`.
2. Checkout calls `POST /v1/access/payment-intents` and polls `GET /v1/access/payment-intents/{payment_intent_id}`.
3. The pass is not issued until payment is settled.
4. Success calls `POST /v1/access/certificates` and displays the Bastion Access Pass exactly once.
5. Import calls `POST /v1/access/challenges`, signs through Vault/device custody, then calls `POST /v1/access/sessions`.
6. Protected pages use Proof-of-Access session state and show locked, upgrade-required, expired, revoked, lockdown, or degraded states before premium data is requested.

## Safety boundaries

- No login/register/password auth is active in the frontend migration path.
- No mandatory email field is required for authentication.
- The raw Bastion Access Pass must not be sent to analytics, placed in URLs, or stored in browser localStorage.
- This is not your Bitcoin wallet seed.
- Bastion will never ask for your Bitcoin wallet seed or private key.
- Development signing is only a placeholder for local testing and is disabled in production; production signing requires Vault/device custody.
