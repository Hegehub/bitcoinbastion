# Access Payment Provider Interface

This document describes the payment-provider foundation for Bastion Proof-of-Access Auth. Payment proof is not login: invoice creation only proves that a payment request exists, while a trusted settled provider event is required before later prompts may issue an Access Certificate or Subscription Entitlement.

## PaymentProvider protocol

Payment providers implement:

- `create_invoice(plan_code, amount_sats, metadata)`
- `get_invoice_status(provider_invoice_id)`
- `verify_webhook(payload, headers)`
- `parse_webhook_event(payload, headers)`

Providers return redacted value objects only. They must not expose provider API keys, webhook secrets, payer identity data, raw invoice payloads, raw Access Passes, session material, recovery material, Bitcoin seeds, or wallet private keys.

## Supported states

Internal Access payment intent states are:

- `pending`
- `invoice_created`
- `paid`
- `expired`
- `invalid`
- `cancelled`
- `failed`
- `paid_late_review_required`
- `manual_review_required`

## State transition table

| From | To | Rule |
| --- | --- | --- |
| `pending` | `invoice_created` | Created after trusted provider invoice creation. |
| `invoice_created` | `paid` | Only after verified settled provider event/status. |
| `invoice_created` | `expired` | Explicit expiration path. |
| `invoice_created` | `invalid` | Verified invalid provider event. |
| `invoice_created` | `cancelled` | Explicit internal cancellation. |
| `expired` | `paid_late_review_required` | Late settled event requires explicit review. |
| `invalid` / `cancelled` | `manual_review_required` | Settled event after final problem state requires review. |
| `paid` | `paid` | Duplicate settled events are idempotent and tagged. |
| `paid` | `expired` / `invalid` / `cancelled` | Rejected. |

## Idempotency requirements

Duplicate settled events must not create duplicate payment records or later certificate issuance. The service annotates duplicate events in redacted metadata and returns the existing paid intent.

## Manual grant restrictions

`ManualGrantProvider` exists for tests, local development, controlled emergency/admin grants, and enterprise/manual contract grants. It is disabled by default with `ACCESS_ALLOW_MANUAL_GRANTS=false`. Manual grants do not support public webhooks and do not mark invoices paid automatically.

If manual grants are enabled in production, the provider emits a clear security warning. Public endpoints must not expose manual grant behavior without admin/internal authorization and audit logging.

## Privacy model

Payment metadata is redacted before storage. Sensitive keys including API keys, secrets, webhook data, email, IP, name, address, raw pass/session/recovery values, seed material, and private-key material are replaced with `[REDACTED]`.

Payment storage is not an identity database. It does not require `user_id`, email, username, password, Bitcoin seed, or wallet private-key fields.

## Future Access Certificate issuing

This layer stops at verified payment state. Future prompts will use verified settled payment intents as one input to Access Certificate and Subscription Entitlement issuance, alongside device key binding, signatures, revocation checks, and audit events.
