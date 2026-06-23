# Developer Guide

This guide consolidates the developer-facing documentation for Bitcoin Bastion. It covers the official SDKs, integration surfaces, safety guidelines, and the developer layer hardening audit.

## SDK Overview

### Python SDK

The Python SDK (located in `sdk/python`) provides `BastionClient` and `AsyncBastionClient` classes for accessing Bitcoin Bastion API endpoints. The client includes helpers for webhook signature verification and WebSocket subscriptions. It is a developer preview and not a custodial wallet.

To install and test the Python SDK, run:

```bash
make sdk-python-check
```

### TypeScript SDK

The TypeScript SDK (published as `bitcoin-bastion-sdk` in `sdk/typescript`) exposes resources for signals, news, onchain, trace, evidence, market context, provider health, webhooks and WebSocket streams. Install dependencies and run tests with:

```bash
cd sdk/typescript
npm install
npm run typecheck
npm test
```

The client is initialised with a base URL, API key and timeout settings. SDKs reject sensitive inputs and never implement key import, wallet-file upload or transaction signing.

### Hardening Notes

Both SDKs are convenience clients. They do not hold or transmit private keys, seed phrases or other signing material. They provide safety helpers such as constant-time HMAC signature verification for webhooks and bound payload size limits.

## Integration Surfaces

Integrators should use the appropriate surface for their workflow:

- Use REST/SDK calls for synchronous request/response interactions.
- Use WebSockets for live dashboards and bounded monitoring.
- Use webhooks for signed asynchronous notifications with replay and timestamp verification.
- Use MCP tools for local-agent, read-only, recommendation and draft-only workflows.

Most REST APIs return a `{ data, error, meta }` envelope. SDK clients unwrap the `data` field by default.

## Safety Guidelines

Bitcoin Bastion is Bitcoin-first, evidence-driven and operator-controlled. Integrators must never submit seed phrases, private keys, wallet files or signing material. Trace outputs are advisory-only and not legal verification or Bitcoin consensus proof; market intelligence and historical similarity provide correlation-based context and are not financial advice.

SDKs reject sensitive inputs before sending requests and enforce timestamp tolerance and replay protection on webhook signatures.

Treasury actions require explicit operator approval. SDKs do not sign or broadcast Bitcoin transactions.

## Developer Layer Hardening Audit

A recent audit assessed the developer layer across the event system, webhooks, WebSocket streams, SDKs, CLI, MCP connector and plugin API. The audit confirmed:

- Sensitive wallet material is rejected or redacted by event payload validation, webhook payload validation, WebSocket serialization and SDK safety helpers.
- Event payloads and metadata have explicit size limits, and event types and identifiers are bounded.
- Webhook signatures require verification of timestamp, delivery ID, event name and HMAC signature.
- Webhook URLs are validated to reject empty, malformed or local/private network targets.
- WebSocket topic subscriptions and payloads are bounded and redacted.
- CLI and MCP tools remain read-first and do not expose signing or transaction broadcasting.
- Plugin permissions are least-privilege and deny-by-default, with forbidden custody or signing permissions rejected.
- Metric labels are bounded to avoid leaks of raw URLs, addresses or delivery IDs.

Production blockers identified include finalising authentication, rate limiting, TLS and deployment evidence, WebSocket authentication for private streams, and secure package signing for external plugins.

## Choosing the Right Tool

When building or integrating on Bitcoin Bastion:

- Use the Python or TypeScript SDKs where possible for safe convenience.
- Use REST calls for generic HTTP clients or languages without an SDK.
- Use WebSocket streams to follow live events or market updates.
- Use webhooks to receive asynchronous notifications; always verify signatures and enforce timestamp tolerance.
- Use the MCP connector for local offline assessment and draft-only operations.

Never bypass safety guidelines or operate on sensitive wallet material. Bitcoin Bastion is designed to keep custody with the operator and provide evidence-driven context without automating value transfer.
