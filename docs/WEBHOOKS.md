# Webhooks

Bitcoin Bastion webhook management is an operator/developer configuration layer for event notifications. It lets operators define webhook endpoints, subscribe those endpoints to registered event types, inspect delivery records, and create safe test delivery records.

## Current status

Webhook management API: implemented foundation.

Signed webhook test deliveries and delivery-log hardening: implemented foundation.

This prompt does **not** perform outbound HTTP delivery, retry dispatch, or worker execution. HMAC signing helpers, canonical headers, and replay-protection verification utilities are implemented for prepared delivery records.

## No-custody warning

Webhooks are event notification mechanisms only. Webhooks do not receive seed phrases, private keys, wallet files, keystore blobs, xprv/yprv/zprv material, or signing material. Webhooks must not be used as transaction signing channels. Treasury events are notification/draft/review workflow events only unless a later explicit approval workflow exists.

## Endpoint lifecycle

Webhook endpoints have these statuses:

- `active`
- `disabled`
- `failing`
- `deleted`

Deletes are soft deletes. A deleted endpoint is disabled and hidden from normal listing/get operations.

## Event subscriptions

Each endpoint can subscribe to one or more registered Bitcoin Bastion event types. Duplicate subscriptions for the same endpoint and event type are rejected. Event type validation is backed by the canonical event registry.

The default test event is `webhook.test`.

## Test delivery behavior

`POST /api/v1/webhooks/{webhook_id}/test` creates a signed `webhook_deliveries` row with status `test_created`, canonical `X-Bastion-*` headers, and a request-body hash. It does not open a network connection and does not retry delivery.

## Delivery statuses

- `pending`
- `test_created`
- `delivered`
- `failed`
- `retry_scheduled`
- `retrying`
- `dead`
- `skipped`

The management API creates `test_created` records. The Celery dispatcher creates signed `pending` delivery attempts, records `delivered`, `failed`, or `retry_scheduled` outcomes, and moves exhausted attempts to terminal outbox dead-letter state.

## Limitations

- HMAC SHA256 signatures and `X-Bastion-*` headers are implemented for prepared delivery and test-delivery records.
- Celery webhook dispatcher execution is implemented for outbox-backed delivery. Operator runbooks, live delivery SLO evidence, and secret rotation remain pending later prompts.
- WebSocket streaming, SDK consumption, CLI commands, MCP connectors, and plugin delivery are separate future prompts.
- Private-network and localhost target URLs are rejected by default.
- Raw webhook signing secrets are not returned by the API; only `secret_ref` and `secret_available` metadata are exposed. Rotation remains a later prompt.
## Webhook signing and delivery observability

Bitcoin Bastion webhook delivery security is implemented as a no-custody notification layer. Webhooks are event notifications only: they never carry seed phrases, private keys, wallet files, keystore files, signing material, transaction-signing instructions, or custody authority.

### Event envelope

Every signed delivery body is deterministic JSON with this shape:

```json
{
  "id": "event_or_outbox_id",
  "event_type": "signal.published",
  "payload_version": 1,
  "created_at": "2026-06-08T00:00:00Z",
  "data": {},
  "limitations": [],
  "source": "bitcoin-bastion"
}
```

Payloads must preserve advisory and safety limitations. Trace payloads are not legal verification or Bitcoin consensus proof. Market and signal payloads are not financial advice.

### Required headers

Each prepared webhook delivery includes these canonical headers:

```text
X-Bastion-Event: <event_type>
X-Bastion-Timestamp: <unix_timestamp_seconds>
X-Bastion-Delivery-ID: <uuid>
X-Bastion-Event-ID: <event_id>
X-Bastion-Signature: v1=<hex_hmac_sha256>
X-Bastion-Payload-Version: <payload_version>
X-Bastion-Source: bitcoin-bastion
```

### HMAC SHA256 algorithm

The signature is calculated with the endpoint's server-side signing secret. Bitcoin Bastion does not expose the stored signing secret in list, get, delivery, or test responses.

Canonical signing payload:

```text
<timestamp>.<raw_json_body>
```

Python receiver example:

```python
import hashlib
import hmac
import time


def verify_bastion_webhook(secret, headers, raw_body):
    signature = headers["X-Bastion-Signature"]
    timestamp = int(headers["X-Bastion-Timestamp"])
    delivery_id = headers["X-Bastion-Delivery-ID"]
    event_id = headers["X-Bastion-Event-ID"]

    # Store delivery_id server-side to reject replayed delivery ids.
    if abs(int(time.time()) - timestamp) > 300:
        return False

    message = f"{timestamp}.{raw_body}".encode("utf-8")
    expected = "v1=" + hmac.new(
        secret.encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)
```

Receivers should store recently seen `X-Bastion-Delivery-ID` values and reject duplicates to provide receiver-side replay protection. Bitcoin Bastion verifies signatures with a default five-minute timestamp tolerance in its helper utilities.

### Delivery logs

Webhook delivery attempts are persisted with delivery id, event id through the outbox link, event type, status, target URL, signed request headers, request-body SHA256 hash, bounded response preview, bounded sanitized error message, attempt number, duration, and retry timestamps. The raw request body is not persisted in delivery logs; only its hash and storage metadata are retained. Response and error previews are capped at 1000 characters and sensitive-looking material is redacted.

Delivery statuses include `pending`, `test_created`, `delivered`, `failed`, `retry_scheduled`, `retrying`, `dead`, and `skipped`. Retry scheduling is deterministic exponential backoff: default initial delay 30 seconds, maximum delay 3600 seconds, and default maximum attempts 8.

### Test delivery endpoint

`POST /api/v1/webhooks/{id}/test` creates a signed `webhook.test` delivery record using the same signing mechanism as normal deliveries. It returns the delivery id, event type, signed headers, request-body hash, and `network_delivery_attempted: false`. It does not send a network request in this prompt.

Test delivery data:

```json
{
  "message": "Bitcoin Bastion webhook test delivery.",
  "advisory": true,
  "no_custody": true
}
```

### Current limitations

- Webhook management and signed test delivery are implemented.
- Outbound dispatcher execution and retry/backoff are implemented through the outbox worker. Secret rotation, live operational evidence, and production delivery SLOs remain pending later prompts.
- Webhooks are not payment approval, legal verification, Bitcoin consensus proof, or transaction-signing channels.

## Dispatcher lifecycle

Webhook delivery follows the durable event flow:

```text
Domain service -> publish_event(...) -> event_outbox -> dispatch_webhook_outbox_events -> signed webhook POST -> delivery log
```

The dispatcher reads ready `pending` outbox rows, resolves active endpoints subscribed to the event type, signs one POST per endpoint, records each delivery attempt, and updates the outbox row. Events with no subscribers are marked dispatched with no network attempt. 2xx responses are delivered. 3xx and 4xx responses are terminal delivery failures for that endpoint. 5xx responses, timeouts, and network errors are retryable until the event reaches maximum attempts. Sensitive payload material blocks delivery and moves the outbox row to dead letter with a sanitized error.

Webhook events are infrastructure notifications only. They are not legal verification, financial advice, Bitcoin consensus proof, or authorization to execute transactions.

## Python SDK helper

The developer-preview Python SDK includes `bitcoin_bastion_sdk.webhooks.verify_signature(...)` for receiver-side HMAC verification. The helper uses the same timestamp and raw-payload HMAC contract documented above and does not log webhook secrets.

## TypeScript SDK helper

The TypeScript SDK exposes `client.webhooks.*` for webhook management and `verifyBastionWebhookSignature(...)` for HMAC SHA256 receiver verification. Receivers should verify timestamps and retain recent delivery IDs for replay protection.

## Replay-resistant verification

Webhook receivers must verify all signed fields before processing a delivery:

- `X-Bastion-Event`
- `X-Bastion-Timestamp`
- `X-Bastion-Delivery-ID`
- `X-Bastion-Signature`
- the exact raw request body bytes

The signature covers `timestamp.delivery_id.event_type.raw_body`. Receivers should reject stale timestamps, missing delivery IDs, malformed signatures, invalid HMACs, and duplicate delivery IDs. Persist delivery IDs on the receiver side to prevent repeated processing.

Private-network webhook targets are rejected by default. Local/self-hosted development can opt in with `BB_WEBHOOK_ALLOW_PRIVATE_NETWORK_TARGETS=true`, but this should not be enabled for production exposure without network egress controls.
