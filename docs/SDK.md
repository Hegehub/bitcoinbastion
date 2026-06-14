# SDKs

## Python SDK

The Python SDK lives in `sdk/python` and is currently a developer preview. It provides `BastionClient` and `AsyncBastionClient` for existing Bitcoin Bastion API endpoints plus webhook signature verification and WebSocket subscription helpers.

Bitcoin Bastion is no-custody. Never submit seed phrases, private keys, wallet files, xprv/yprv/zprv, or signing material. Trace is advisory-only, not legal verification, and not Bitcoin consensus proof. Market intelligence is not financial advice.

Run SDK checks with:

```bash
make sdk-python-check
```

## TypeScript SDK

A developer-preview TypeScript SDK is available under `sdk/typescript` and documented in [`TYPESCRIPT_SDK.md`](TYPESCRIPT_SDK.md). It exposes REST resources, WebSocket helpers, webhook signature verification, ResponseEnvelope unwrapping, and no-custody safety checks.

## Hardening notes

The Python and TypeScript SDKs are convenience clients. They are not custody tools, not wallets, not signing interfaces, and not trading executors. SDK examples must not include seed phrases, private keys, wallet files, xprv/yprv/zprv material, or signing material. Webhook verification helpers require timestamp, delivery id, event type, raw payload, shared secret, HMAC SHA256, and constant-time comparison.
