# Developer Layer Hardening Audit

Status: **developer hardening baseline complete; production evidence still required**.

## Scope

Audited areas include events/outbox, webhooks, WebSocket streams, Python and TypeScript SDKs, CLI, MCP connector, plugin foundation, and developer-facing documentation.

## Findings and hardening actions

- Sensitive wallet material is rejected or redacted by event payload safety checks, webhook payload validation, WebSocket serialization, SDK safety helpers, CLI safety tests, MCP safety tests, and plugin permission checks.
- Event payload and metadata limits are explicit: payloads default to 65,536 bytes, metadata defaults to 16,384 bytes, event types and aggregate identifiers are length bounded, and long string fields fail safely.
- Webhook signatures are replay-resistant: receivers must verify `X-Bastion-Timestamp`, `X-Bastion-Delivery-ID`, `X-Bastion-Event`, `X-Bastion-Signature`, and the exact raw body.
- Webhook URLs reject empty, malformed, non-HTTP(S), embedded-credential, localhost, and private-network targets by default. Private-network targets require explicit local-development configuration.
- Webhook delivery retries are bounded, error messages are sanitized/truncated, and non-2xx responses are not treated as successful delivery.
- WebSocket topic subscriptions are bounded and invalid topics are rejected; payload serialization redacts sensitive material and truncates oversized payloads.
- MCP tools remain read, draft, recommendation, or explanation oriented.
- CLI commands remain read-first/operator-safe and do not expose signing or transaction broadcasting commands.
- Plugin permissions are explicit, least-privilege, deny-by-default, and forbidden custody/signing permissions are rejected.
- Metrics use bounded labels for developer-layer webhook and WebSocket counters and avoid raw URLs, addresses, payloads, delivery IDs, and event IDs.

## Production blockers

- Production auth/rate-limit/TLS/deployment evidence is still required before internet exposure.
- WebSocket authentication is still a production-hardening item for private/operator streams.
- External plugin package loading remains disabled until package signing, operator approval persistence, and security review gates exist.
- Receivers must persist delivery IDs to prevent duplicate processing beyond timestamp/HMAC verification.
