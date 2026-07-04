# Bastion Access Layer

## BTCPay Server provider role

BTCPay Server is a production payment provider for Bastion Proof-of-Access payment intents. Payment is not login, and invoice creation is not entitlement. A created invoice only starts the Payment Proof Layer; it does not issue an Access Certificate, Subscription Entitlement, session, API key, or bearer-style credential.

Only a verified settled BTCPay webhook or trusted provider status check may mark an Access payment intent as paid. Future certificate issuing must use the paid state as an input alongside device-key binding, signed certificate material, revocation checks, and audit events.

## Security requirements

- `ACCESS_BTCPAY_ENABLED` is disabled by default.
- `ACCESS_BTCPAY_WEBHOOK_SECRET` is required for webhook verification in production.
- `ACCESS_BTCPAY_API_KEY` and webhook secrets must come from a secret manager or Kubernetes secret in production.
- No email or password is required for payment intent creation.
- Bastion never asks for a Bitcoin seed phrase or Bitcoin private key.
- Raw webhook bodies, API keys, checkout secrets, Access Pass values, session tokens, and recovery material must not be logged.

## Per-request Proof-of-Possession signatures

Protected Access requests must not rely on `Authorization: Bearer` or on `X-Bastion-Session` alone. A protected request must include:

- `X-Bastion-Session`
- `X-Bastion-Timestamp`
- `X-Bastion-Nonce`
- `X-Bastion-Body-Hash`
- `X-Bastion-Signature`

The canonical request digest is newline-delimited as `METHOD`, path, body hash, timestamp, and nonce. The verifier checks the body hash, enforces timestamp skew, records a per-session nonce hash for replay protection, and verifies the request signature with the bound device public key. Raw session tokens, signatures, nonces, Access Pass values, recovery material, and request bodies must not be logged.

## Operational troubleshooting

| Symptom | Expected handling |
| --- | --- |
| Invalid webhook signature | Reject the webhook as `payment_webhook_invalid`; do not mark payment paid. |
| Expired invoice | Mark the intent expired unless it is already paid. |
| Provider unavailable | Return a safe provider-unavailable error without leaking API details. |
| Duplicate webhook | Treat duplicate settled events idempotently; do not issue duplicate downstream certificates. |
| Unpaid invoice | Do not issue Access Certificates or Subscription Entitlements. |

## Legacy authentication disabled

Bitcoin Bastion uses Proof-of-Access authorization for protected APIs. Legacy email/password authentication is disabled.

- `/api/v1/auth/register` no longer creates password accounts.
- `/api/v1/auth/login` no longer authenticates username/password credentials and never issues bearer/JWT access tokens.
- `Authorization: Bearer` is rejected as Proof-of-Access credential material.
- Protected APIs must use Proof-of-Access sessions, per-request signatures, revocation checks, and policy decisions.
- Bastion will never ask for a Bitcoin seed phrase or Bitcoin private key for authentication or recovery.
