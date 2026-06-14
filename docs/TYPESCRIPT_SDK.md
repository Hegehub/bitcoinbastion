# TypeScript SDK

The `bitcoin-bastion-sdk` package under `sdk/typescript` is a developer-preview TypeScript client for Bitcoin Bastion APIs.

Bitcoin Bastion is no-custody. Never submit seed phrases, private keys, wallet files, xprv/yprv/zprv, or signing material. Trace outputs are advisory-only, not legal verification, and not Bitcoin consensus proof. Market intelligence is informational and not financial advice.

## Install and verify

```bash
cd sdk/typescript
npm install
npm run typecheck
npm test
```

## Client

```ts
import { BitcoinBastionClient } from "bitcoin-bastion-sdk";

const client = new BitcoinBastionClient({
  baseUrl: "http://localhost:8000",
  apiKey: process.env.BASTION_API_KEY,
  timeoutMs: 5000,
});
```

The client exposes signals, news, onchain, trace, evidence, market, treasury, policy, wallet, provider health, webhooks, and WebSocket resources.

## Safety

The SDK rejects sensitive inputs before sending requests to Trace, treasury, policy, and wallet helpers. It does not implement key import, wallet-file upload, seed phrase handling, PSBT signing, transaction signing, trading execution, or custody features.

## Endpoint mapping

- Trace: `/api/v1/trace/*` and `/api/v1/public/trace/{report_id}/summary`.
- Signals: `/api/v1/signals/*`.
- Evidence: `/api/v1/evidence/packets/*`.
- Market context: `/api/v1/market/btc/context` and intelligence timeline/candle routes.
- Provider health: `/api/v1/health/runtime`, `/api/v1/health/providers`, `/api/v1/health/degraded`.
- Webhooks: `/api/v1/webhooks/*`.
- WebSockets: `/api/v1/ws/*`.

## Webhooks

`verifyBastionWebhookSignature` verifies HMAC SHA256 `v1=` signatures using the raw payload and timestamp. Receivers should also enforce timestamp tolerance and store delivery IDs for replay protection.
