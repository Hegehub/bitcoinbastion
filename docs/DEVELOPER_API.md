# Developer API Baseline

Bitcoin Bastion's developer/API layer is currently an internal foundation. The event publisher writes validated domain events into the durable Event Outbox so future webhook, WebSocket, SDK, CLI, MCP, and plugin prompts can consume one shared contract.

## Current state

- Internal event taxonomy and registry are implemented.
- Event Outbox persistence is implemented.
- The internal event publisher records outbox rows for selected domain workflows.
- Outbox-backed webhook delivery dispatcher and signed delivery logs are implemented; production environment hardening remains required.
- Generic and specialized WebSocket streaming foundations are implemented with an in-process broker.
- The Python SDK and operator-safe CLI are implemented as developer-preview surfaces; MCP connector and plugin runtime consumption are not implemented yet.

## Safety posture

Event publication is no-custody and advisory-only. Payloads must not contain wallet secrets, credentials, authorization headers, provider credentials, or signing inputs. Event publication is not proof of payment, legal status, Bitcoin consensus proof, or trading signal correctness.

## Example

```python
publish_event(
    "signal.published",
    {"signal_id": 123, "limitations": ["not_financial_advice"]},
    aggregate_type="signal",
    aggregate_id=123,
    source="signal_governance",
)
```

This records a pending internal outbox row. The webhook dispatcher task later reads ready outbox rows and delivers only to subscribed webhook endpoints; domain services must not call webhooks directly.

## Webhook Management API

Webhook management is implemented as a configuration foundation under `/api/v1/webhooks`. Operators can create endpoints, manage event subscriptions, inspect delivery records, and create safe test delivery records.

Outbound webhook dispatcher execution is implemented through the event outbox. The test endpoint creates a signed delivery record with canonical `X-Bastion-*` headers; SDK and CLI surfaces expose webhook management, test delivery, and delivery-history inspection. MCP delivery and plugin execution remain pending. WebSocket streams are implemented as an in-process foundation and still require production auth/rate-limit hardening before broad exposure.

## Webhook authentication and verification

Webhook test delivery records now use HMAC SHA256 signatures with canonical `X-Bastion-*` headers. Receivers should verify `X-Bastion-Signature` over `<timestamp>.<raw_json_body>`, enforce the default five-minute timestamp tolerance, and store recent delivery IDs to prevent replay. The webhook signing secret is server-side only and is not returned by list, get, delivery-history, or test-delivery responses. Retry workers run through the outbox dispatcher; webhooks are notification channels only and do not carry custody material or transaction-signing authority.
## WebSocket Streams

The generic event stream is available at `/api/v1/ws/events`. Clients may pass `topics=signals,trace,market` to filter messages. Specialized streams are available at `/api/v1/ws/signals`, `/api/v1/ws/news`, `/api/v1/ws/onchain`, `/api/v1/ws/market`, `/api/v1/ws/trace`, `/api/v1/ws/treasury`, `/api/v1/ws/provider-health`, and `/api/v1/ws/intelligence-timeline`.

Use WebSockets for live dashboards and operator monitoring. Use webhooks for durable signed HTTP notification workflows with retry and delivery logs. Both surfaces consume the Event Outbox/Event Bus foundation and must not bypass it. Streams emit system, heartbeat, error, and event envelopes. Payloads are sanitized, no-custody metadata is preserved, and `last_event_id` replay currently returns `replay.not_available` rather than fake replay data. Production auth and rate-limit hardening remain required before exposing operator-only streams broadly.

## Python SDK

The developer-preview Python SDK is available under `sdk/python`. It exposes `BastionClient`, `AsyncBastionClient`, webhook signature verification helpers, no-custody safety checks, and WebSocket subscription helpers for the existing Developer/API layer. See [`SDK.md`](SDK.md) and [`../sdk/python/README.md`](../sdk/python/README.md).

## Operator CLI

The operator-safe CLI is available as `bastion` after editable install. It uses the Python SDK as its primary API interface, preserves no-custody safety checks, keeps treasury commands read-only, and is documented in [`CLI.md`](CLI.md).
