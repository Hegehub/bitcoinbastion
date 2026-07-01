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

## Operational troubleshooting

| Symptom | Expected handling |
| --- | --- |
| Invalid webhook signature | Reject the webhook as `payment_webhook_invalid`; do not mark payment paid. |
| Expired invoice | Mark the intent expired unless it is already paid. |
| Provider unavailable | Return a safe provider-unavailable error without leaking API details. |
| Duplicate webhook | Treat duplicate settled events idempotently; do not issue duplicate downstream certificates. |
| Unpaid invoice | Do not issue Access Certificates or Subscription Entitlements. |
