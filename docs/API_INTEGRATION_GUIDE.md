# API Integration Guide

Bitcoin Bastion integrations should prefer the official SDKs where possible:

- Python SDK: `sdk/python`.
- TypeScript SDK: `sdk/typescript`.
- Operator CLI: `cli/bastion_cli`.
- MCP connector: `mcp`.

All integrations must preserve no-custody and advisory semantics. Do not submit seed phrases, private keys, wallet files, xprv/yprv/zprv, or signing material.

## Choosing an integration surface

- Use REST/SDK calls for request/response workflows.
- Use WebSockets for live dashboards and bounded operator monitoring.
- Use webhooks for signed external notifications and retryable delivery logs.
- Use MCP for local-agent, read-only, recommendation-only, and draft-only workflows.

## Response envelopes

Most REST APIs return `{ data, error, meta }`. SDKs unwrap `data` by default and expose raw transport helpers for operators who need the full envelope.

## Safety language

Trace outputs are advisory-only, not legal verification, and not Bitcoin consensus proof. Market intelligence is informational and not financial advice. Evidence packets are replayable context artifacts and do not prove causation.
