# API Access

Bitcoin Bastion uses Proof-of-Access authorization for protected APIs. Legacy email/password authentication is disabled.

Protected API callers must follow the Access flow:

1. create a payment intent with `/api/v1/access/payment-intents`;
2. issue an Access Certificate and Subscription Entitlement after verified payment;
3. create an origin-bound challenge;
4. sign the challenge with a bound local device key;
5. create a short-lived Proof-of-Possession session;
6. sign protected requests with the required `X-Bastion-*` headers.

Required protected request headers are `X-Bastion-Session`, `X-Bastion-Timestamp`, `X-Bastion-Nonce`, `X-Bastion-Body-Hash`, and `X-Bastion-Signature`.

`Authorization: Bearer` is not accepted as Proof-of-Access, and an Access Pass is never a bearer token.

## Protected endpoint enforcement

Premium/private endpoints are classified in `docs/ACCESS_PROTECTED_ENDPOINTS_MATRIX.md`. Protected requests use Access dependencies rather than legacy `get_current_user`, JWT, or `Authorization: Bearer`.

Access denials are intentionally structured as `access_required`, `upgrade_required`, `scope_required`, `metric_not_allowed`, `quota_exceeded`, `revoked`, `expired`, or `step_up_required` depending on the failed gate. Critical actions require signed request headers and may also require `X-Bastion-Intent-Signature`.

## Access recovery API

Proof-of-Access recovery uses a Bastion Recovery Seed / Access Recovery Phrase and plan-specific quorum rules. This is NOT your Bitcoin wallet seed. Never enter your Bitcoin wallet seed into Bastion. Bastion will never ask for your Bitcoin seed or private keys. This phrase restores access rights only, not Bitcoin funds.

Recovery endpoints:

- `POST /api/v1/access/recovery/setup` returns display-once Bastion recovery phrase material and stores only commitments.
- `POST /api/v1/access/recovery/start` creates a recovery attempt with cooldown and required quorum metadata.
- `POST /api/v1/access/recovery/factors` submits one recovery factor without logging or storing raw factor text.
- `GET /api/v1/access/recovery/status/{recovery_attempt_id}` returns threshold status without revealing which secret failed.
- `POST /api/v1/access/recovery/complete` completes recovery only after quorum, cooldown, revocation, and policy checks pass.
- `POST /api/v1/access/recovery/rotate` rotates recovery material after a protected Access ceremony.
- `POST /api/v1/access/recovery/cancel` cancels an active recovery attempt.

Pro recovery requires 2-of-3 factors, Business requires 2-of-3 factors, and Enterprise requires 3-of-5 factors. Recovery never accepts password fallback, email-only recovery, support-only reset, raw Access Pass bearer proof, Bitcoin seed phrases, Bitcoin private keys, xprv material, or wallet seed imports.
