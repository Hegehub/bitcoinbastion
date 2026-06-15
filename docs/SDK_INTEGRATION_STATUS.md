# SDK Integration Status

Status vocabulary: **implemented**, **partially implemented**, **planned**, **blocked**, **not applicable**.

## Python SDK

Status: **implemented**.

The Python SDK package contains client, auth, errors, webhook signature verification, WebSocket subscriptions, typed resource modules, and schema modules for signals, news, on-chain, Trace, treasury, and wallet workflows.

Safety status: **implemented**. Trace batch/address helpers call safety guards that reject seed phrases, private keys, extended private keys, wallet files, keystores, and signing material before API submission.

## TypeScript SDK

Status: **implemented**.

The TypeScript SDK includes package metadata, a typed client, resource wrappers, ResponseEnvelope-style unwrapping through the client layer, WebSocket helpers, and safety rejection for sensitive Trace inputs.

## CLI

Status: **implemented at smoke level**.

The CLI package exists and supports read-first operator workflows. This pass verifies presence and safety posture; it does not certify every command against a live backend.

## MCP Connector

Status: **implemented at smoke level**.

The MCP connector package exists for read/draft/recommendation workflows. Risky execution remains outside the MCP connector and requires operator review.

## Remaining SDK Blockers

- Live backend compatibility smoke requires a running API and environment-specific credentials.
- TypeScript package tests/build require the local Node dependency environment.
