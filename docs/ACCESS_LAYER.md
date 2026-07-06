# Bastion Access Layer

The Bastion Access Layer implements the **Proof‑of‑Access** authentication model.  It replaces legacy account registration and password login with a flow based on payment proof, signed certificates, subscription entitlements, device keys and origin‑bound sessions.  There is no bearer token and no user database.  Proof‑of‑Access is intentionally non‑custodial: it never asks for Bitcoin seed phrases or private keys, and the backend never stores your device keys.

## Overview and motivation

* **No email/password.**  Personal information is not collected and there is no account database.  Authentication is based on possession of a signed certificate and a device key.
* **No bearer tokens.**  A raw Access Pass is never a password; it is used once to issue a certificate and subscription entitlement.  Sessions are bound to the device key and origin and must be signed per request.
* **No wallet seeds.**  Bitcoin wallet seeds or private keys must never be used for authentication.  Bastion will never ask for your Bitcoin seed, xprv/yprv/zprv or private key.
* **Entitlement by payment proof.**  A user purchases a plan by creating a payment intent and paying the invoice.  Payment is not login; it merely authorizes the issuance of a certificate.
* **Device possession.**  The client generates a long‑term device keypair.  Only possession of the private key allows the user to sign challenges and requests.

## High‑level flow

1. **Create payment intent.**  The client calls `POST /api/v1/access/payment-intents` with the desired plan code.  This returns a `payment_intent_id` and, if using BTCPay, a checkout URL.
2. **Pay invoice.**  The user pays the invoice.  Bastion monitors settlement via provider webhooks.  Payment is not a login.
3. **Verify payment proof.**  The client polls `GET /api/v1/access/payment-intents/{id}` until the `status` becomes `paid`.
4. **Issue access certificate.**  The client generates a device keypair and calls `POST /api/v1/access/certificates`.  The issuer signs a certificate binding the plan, device key and expiry.
5. **Issue subscription entitlement.**  The certificate grants a subscription entitlement that defines plan code, scopes, metric entitlements, limits and expiry.  The entitlement is signed by the issuer.
6. **Create origin‑bound challenge.**  The client calls `POST /api/v1/access/challenges` with the certificate fingerprint, origin and requested scopes.  The server returns a challenge payload.
7. **Sign challenge.**  The client signs the challenge with its private device key and submits the signature via `POST /api/v1/access/sessions`.  A short‑lived session token is returned.
8. **Sign protected requests.**  Each protected API request must include `X‑Bastion‑Session`, `X‑Bastion‑Timestamp`, `X‑Bastion‑Nonce`, `X‑Bastion‑Body‑Hash` and `X‑Bastion‑Signature`.  See `docs/ACCESS_REQUEST_SIGNING.md` for details.
9. **Policy and revocation checks.**  The server verifies the signature, checks revocation status, enforces plan and scope policies, applies limits and returns the response.

## Plans, scopes and metric entitlements

| Code | Description |
| --- | --- |
| `lite_pass` | Free or very low‑limit access for exploration. |
| `basic_pass` | Basic analytics and trace. |
| `plus_pass` | Adds more metrics and daily credit allowances. |
| `pro_pass` | For advanced users; may allow delegated passes. |
| `business_pass` | For teams with shared workspace and recovery quorum. |
| `enterprise_pass` | Highest tier with custom limits and offline validity packs. |

Each plan is bound to a subscription period (e.g. 30 days) and a set of scopes and metric entitlements.  **Scopes** are stable strings identifying functional areas (e.g. `trace:lite`, `citadel:report`).  **Metric groups** bundle related metrics and carry costs.  A subscription entitlement includes a budget of daily or monthly metric credits and request rate limits.  Upgrades require paying for a higher‑tier plan; downgrades take effect at the next renewal.

## Revocation, audit and lockdown

* **Revocation registry.**  Certificates or sessions can be revoked if compromised, expired, refunded or in violation of policy.  Revocations cascade to child API keys and delegated passes.
* **Audit chain.**  All access events are recorded on an append‑only audit chain with cryptographic hashes.  Operators and users can verify when and how a session was used.
* **Lockdown.**  The `POST /api/v1/access/lockdown` endpoint can freeze a pass, workspace or linked devices.  It revokes sessions, child keys and delegated passes and emits tamper‑evident audit events.  Some scopes may require a human‑intent signature.  See `docs/ACCESS_LOCKDOWN_MODE.md`.

## Recovery

Bastion Access Recovery lets you regain control of your pass when all devices are lost.  Each plan includes a **Bastion Recovery Seed** which is **not** a Bitcoin wallet seed.  The seed is used only to rebind a certificate.  Recovery requires a quorum of factors (vault signatures, recovery seed, hardware key, etc.) and may be subject to a cooldown.  Support cannot unilaterally recover Pro, Business or Enterprise passes.  See `docs/ACCESS_RECOVERY.md` for full details.

## BTCPay Server provider role

BTCPay Server is a production payment provider for Bastion Proof‑of‑Access payment intents.  Payment is not login, and invoice creation is not an entitlement.  A created invoice only starts the Payment Proof Layer; it does not issue an access certificate, subscription entitlement, session, API key or bearer‑style credential.  Only a verified settled BTCPay webhook or trusted provider status check may mark an Access payment intent as paid.  Future certificate issuing must use the paid state as an input alongside device‑key binding, signed certificate material, revocation checks and audit events.

Security requirements:

- `ACCESS_BTCPAY_ENABLED` is disabled by default.
- `ACCESS_BTCPAY_WEBHOOK_SECRET` is required for webhook verification in production.
- `ACCESS_BTCPAY_API_KEY` and webhook secrets must come from a secret manager or Kubernetes secret in production.
- No email or password is required for payment intent creation.
- Bastion never asks for a Bitcoin seed phrase or Bitcoin private key.
- Raw webhook bodies, API keys, checkout secrets, Access Pass values, session tokens and recovery material must not be logged.

## Per‑request Proof‑of‑Possession signatures

Protected Access requests must not rely on `Authorization: Bearer` or on `X‑Bastion‑Session` alone.  Clients must include the per‑request signing headers described in `docs/ACCESS_REQUEST_SIGNING.md`.  The server verifies the body hash, enforces timestamp skew, records a per‑session nonce for replay protection and verifies the request signature with the bound device public key.  Raw session tokens, signatures, nonces and Access Pass values must never be logged.

## Legacy authentication disabled

Bitcoin Bastion uses Proof‑of‑Access authorization for protected APIs.  The legacy `/api/v1/auth/register` and `/api/v1/auth/login` endpoints remain only as deprecated compatibility stubs that return `legacy_auth_disabled`.  They never create password accounts or issue bearer/JWT tokens.  `Authorization: Bearer` is rejected as proof‑of‑access.  Protected APIs must use Proof‑of‑Access sessions, per‑request signatures, revocation checks and policy decisions.

## Bastion Recovery Seed and recovery quorum

Bastion recovery is accountless access recovery.  It restores access rights only; it is not Bitcoin custody, not Bitcoin multisig and not Bitcoin fund recovery.

Safety copy for every recovery surface:

- This is **not** your Bitcoin wallet seed.
- Never enter your Bitcoin wallet seed into Bastion.
- Bastion will never ask for your Bitcoin seed or private keys.
- This phrase restores access rights only, not Bitcoin funds.

### Recovery profiles

| Plan | Bastion Recovery Seed | Quorum |
| --- | --- | --- |
| Lite | 12‑word Access Recovery Phrase | 1 factor plus cooldown |
| Basic | 12‑word Access Recovery Phrase | 1 factor plus cooldown/audit |
| Plus | 12‑word Access Recovery Phrase | Optional 2‑of‑3 Desktop Vault, Mobile Vault, phrase |
| Pro | 24‑word Access Recovery Phrase | Required 2‑of‑3 Desktop Vault, Mobile Vault, phrase |
| Business | Business Recovery Seed | Required 2‑of‑3 Owner Vault, Admin Vault, Business Recovery Seed |
| Enterprise | 24‑word Access Recovery Phrase | Required 3‑of‑5 Owner Key, Admin Key, Hardware Key, phrase, Offline Recovery Kit |

Recovery APIs are available under `/api/v1/access/recovery/*` for setup, start, factor submission, status, completion, rotation and cancellation.  Raw recovery phrases are returned only for setup/rotation display‑once flows and are never stored.  The database stores HMAC commitments, factor hints, factor types, recovery attempt hashes, cooldown state and audit events only.

Recovery completion checks quorum, cooldown, revocation state and recovery policy before rebinding a device or revoking old sessions.  Support‑only reset, email‑only recovery, password fallback, bearer‑token recovery, Bitcoin wallet seed input, xprv/private‑key import and any Bitcoin transaction signing are prohibited.

## Human Intent Signature

Critical actions use **Human Intent Signature** rather than an opaque challenge approval.  The API creates a canonical manifest describing the exact action, origin, scopes, denied capabilities, target resource hash, risk level, expiry and consequences.  Vault/Desktop/Mobile clients sign the canonical manifest hash with the bound device key, and the signature is single‑use.  See `docs/ACCESS_HUMAN_INTENT_SIGNATURE.md` for details.  Bastion will never ask for a Bitcoin seed or private key for Human Intent Signature.

## Emergency Lockdown Mode

Emergency Lockdown freezes active sessions, child API keys, delegated passes and linked devices for compromised access material while preserving recovery‑only access.  It emits a tamper‑evident `access_lockdown_started` audit event and never deletes payment or audit history.  See `docs/ACCESS_LOCKDOWN_MODE.md`.
