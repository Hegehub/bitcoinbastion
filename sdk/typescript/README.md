# Bitcoin Bastion TypeScript SDK

Developer-preview TypeScript SDK for the Bitcoin Bastion API.

Bitcoin Bastion is no-custody. Never submit seed phrases, private keys, wallet files, xprv/yprv/zprv, or signing material. Trace outputs are advisory-only, not legal verification, and not Bitcoin consensus proof. Market intelligence is informational and not financial advice. Historical similarity does not guarantee future market behavior.

## Install

```bash
npm install bitcoin-bastion-sdk
```

For local development in this repository:

```bash
cd sdk/typescript
npm install
npm run typecheck
npm test
```

## Quickstart

```ts
import { BitcoinBastionClient } from "bitcoin-bastion-sdk";

const client = new BitcoinBastionClient({
  baseUrl: "http://localhost:8000",
  apiKey: process.env.BASTION_API_KEY,
  timeoutMs: 5000,
});

const status = await client.providerHealth.status();
```

## Resources

The client exposes `signals`, `news`, `onchain`, `trace`, `evidence`, `market`, `treasury`, `policy`, `wallet`, `providerHealth`, `webhooks`, and `websocket` resources.

Trace methods validate inputs before requests and preserve this posture: Advisory-only. Not legal verification. Not Bitcoin consensus proof. No custody. Public Bitcoin addresses only. Never enter seed phrases, private keys, wallet files or signing material.

Signals are informational and evidence-based. Signals are not financial advice, do not guarantee future market behavior, and must not be treated as automatic trading instructions.

Treasury methods call existing API approval workflows only when an authenticated operator intentionally invokes them. The SDK does not sign Bitcoin transactions, does not hold keys, and does not custody funds.

## Webhook verification

```ts
import { verifyBastionWebhookSignature } from "bitcoin-bastion-sdk";

const valid = verifyBastionWebhookSignature({
  payload: rawBody,
  signature: headers["x-bastion-signature"],
  timestamp: headers["x-bastion-timestamp"],
  secret: process.env.BASTION_WEBHOOK_SECRET!,
});
```

Webhook events include `X-Bastion-Event`, `X-Bastion-Timestamp`, `X-Bastion-Signature`, and `X-Bastion-Delivery-ID` headers.

## WebSocket streams

```ts
client.websocket.subscribe({
  topics: ["signals", "trace", "market"],
  onEvent: (event) => console.log(event),
  onError: (error) => console.error(error),
});
```

Supported streams include `/ws/events`, `/ws/signals`, `/ws/news`, `/ws/onchain`, `/ws/market`, `/ws/trace`, `/ws/treasury`, `/ws/provider-health`, and `/ws/intelligence-timeline`.

## Endpoint mapping notes

The SDK maps to current repository routes. Evidence packet export uses `/api/v1/evidence/packets/{packet_id}` with `format` query parameters. Market dashboard helpers currently use `/api/v1/market/btc/context`. Wallet health helpers read wallet profile health reports and do not implement wallet import, key handling, PSBT signing, transaction signing, or mnemonic handling.
