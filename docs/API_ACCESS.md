# Access API Contract

All paths below are mounted under `/api/v1`. Examples may omit the `/api` prefix only in SDK shorthand; the live FastAPI OpenAPI paths use `/api/v1/access/*`.

## Common security rules

- Public setup endpoints do not use `Authorization: Bearer`.
- Protected endpoints require `X-Bastion-Session` and, where required, `X-Bastion-Timestamp`, `X-Bastion-Nonce`, `X-Bastion-Body-Hash`, and `X-Bastion-Signature`.
- A Bastion Access Pass is not a bearer token and must not be sent on every request.
- Bastion never accepts Bitcoin seed/private-key material as authentication or recovery proof.

## Live Access endpoints

| Method | Path | Purpose | Required auth |
| --- | --- | --- | --- |
| POST | `/api/v1/access/payment-intents` | Create an invoice/payment intent for a plan. | Public setup; provider policy applies. |
| GET | `/api/v1/access/payment-intents/{payment_intent_id}` | Poll payment status without issuing access. | Public setup for the intent id. |
| POST | `/api/v1/access/certificates` | Issue a certificate and show the raw Access Pass once after settlement. | Paid intent. |
| POST | `/api/v1/access/challenges` | Create an origin-bound one-time challenge. | Certificate/pass reference. |
| POST | `/api/v1/access/sessions` | Create a short-lived PoP session from a signed challenge. | Signed challenge. |
| GET | `/api/v1/access/me` | Return safe current Access subject state. | `X-Bastion-Session`. |
| GET | `/api/v1/access/me/entitlements` | Return current subscription entitlement metadata. | `X-Bastion-Session`. |
| GET | `/api/v1/access/me/limits` | Return current API/metric limits. | `X-Bastion-Session`. |
| POST | `/api/v1/access/lockdown` | Start Emergency Lockdown for the current certificate. | Session plus Human Intent/step-up policy. |

### Example: create payment intent

Request:

```http
POST /api/v1/access/payment-intents
Content-Type: application/json

{"plan_code":"plus_pass","payment_method":"btcpay"}
```

Response shape:

```json
{"payment_intent_id": 123, "plan_code": "plus_pass", "status": "pending", "certificate_available": false}
```

### Example: signed protected request

```http
GET /api/v1/access/me
X-Bastion-Session: sess_...
X-Bastion-Timestamp: 2026-07-07T00:00:00Z
X-Bastion-Nonce: n_...
X-Bastion-Body-Hash: sha256:...
X-Bastion-Signature: sig_...
```

## Live recovery endpoints

| Method | Path | Purpose | Notes |
| --- | --- | --- | --- |
| POST | `/api/v1/access/recovery/setup` | Create Bastion Recovery Seed setup material shown once. | Live. Not a Bitcoin wallet seed. |
| POST | `/api/v1/access/recovery/start` | Start a policy-bounded recovery attempt. | Live. |
| POST | `/api/v1/access/recovery/factors` | Submit one recovery factor. | Live name; maps to seed/share/device factors. |
| GET | `/api/v1/access/recovery/status/{recovery_attempt_id}` | Read quorum/cooldown status. | Live. |
| POST | `/api/v1/access/recovery/complete` | Complete recovery after quorum and cooldown. | Live. |
| POST | `/api/v1/access/recovery/rotate` | Rotate recovery material after protected ceremony. | Live. |
| POST | `/api/v1/access/recovery/cancel` | Cancel active recovery. | Live. |
| POST | `/api/v1/access/recovery/verify-seed` | Verify seed factor. | Planned alias; use `/recovery/factors` today. |
| POST | `/api/v1/access/recovery/verify-share` | Verify share factor. | Planned alias; use `/recovery/factors` today. |
| GET | `/api/v1/access/recovery/status` | Current-session recovery status. | Planned alias; status currently requires attempt id. |

## Other live Access endpoints

Human Intent: `POST /api/v1/access/intents`, `POST /api/v1/access/intents/{intent_id}/verify`, `GET /api/v1/access/intents/{intent_id}`.

Child API keys: `POST /api/v1/access/api-keys`, `GET /api/v1/access/api-keys`, `GET /api/v1/access/api-keys/{key_id}`, `DELETE /api/v1/access/api-keys/{key_id}`, `POST /api/v1/access/api-keys/{key_id}/rotate`, `POST /api/v1/access/api-keys/{key_id}/freeze`.

Delegated passes: `POST /api/v1/access/delegated-passes`, `GET /api/v1/access/delegated-passes`, `GET /api/v1/access/delegated-passes/{delegated_pass_id}`, `DELETE /api/v1/access/delegated-passes/{delegated_pass_id}`, `POST /api/v1/access/delegated-passes/{delegated_pass_id}/freeze`.

BTCPay webhook: `POST /api/v1/access/payments/btcpay/webhook` accepts provider webhook calls and does not issue certificates by itself.

## Stable error codes

The Access contract reserves these structured error codes where applicable: `unpaid_payment_intent`, `invalid_payment_proof`, `payment_not_settled`, `payment_provider_unavailable`, `certificate_not_found`, `certificate_revoked`, `entitlement_expired`, `plan_upgrade_required`, `metric_not_allowed`, `scope_not_allowed`, `invalid_challenge`, `challenge_expired`, `challenge_reused`, `invalid_session`, `session_expired`, `session_revoked`, `invalid_request_signature`, `nonce_reused`, `timestamp_stale`, `recovery_quorum_required`, `bitcoin_seed_rejected`, and `legacy_auth_disabled`.
