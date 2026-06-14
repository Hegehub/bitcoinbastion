# Safety for Developers

Bitcoin Bastion is Bitcoin-first, evidence-driven, operator-controlled, and no-custody.

Never submit seed phrases, private keys, wallet files, xprv/yprv/zprv, keystore files, or signing material. SDKs and MCP tools include safety checks, but integrators remain responsible for upstream input handling.

## Trace

Trace outputs are advisory-only. They are not legal verification and not Bitcoin consensus proof. Use public Bitcoin addresses only.

## Market intelligence

Market intelligence is informational. Historical similarity does not guarantee future market behavior. Candle attribution is correlation-oriented and not proof of causation. Bitcoin Bastion SDKs do not execute trades.

## Treasury

Treasury APIs are operator-control workflows. SDKs do not hold keys, do not sign Bitcoin transactions, and do not custody funds. Risky treasury actions require explicit operator authorization.

## Webhooks and WebSockets

Webhook receivers should verify signatures, enforce timestamp tolerance, and retain delivery IDs for replay protection. WebSocket consumers should treat degraded, fallback, and stale indicators as first-class safety metadata.
