# Bitcoin Bastion TypeScript SDK

Developer-preview TypeScript SDK for the Bitcoin Bastion API. Legacy `apiKey`/`Authorization: Bearer` authentication is disabled; protected requests use Wallet/LNURL-established, device-bound PoP sessions and canonical `Bastion-Request-*` headers.

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
  headers: {
    "X-Bastion-Session": "session",
    "X-Bastion-Timestamp": "2026-07-03T00:00:00Z",
    "X-Bastion-Nonce": "nonce",
    "X-Bastion-Body-Hash": "sha256:...",
    "X-Bastion-Signature": "signature",
  },
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

## Wallet-first + LNURL Proof-of-Access v2

> **Bitcoin Bastion never requires your Bitcoin or Lightning wallet seed, mnemonic, xprv, or wallet private key.**

The SDK orchestrates external-wallet proof and never owns wallet keys. `WalletProofSigner` receives the visible, expiring human intent; `LnurlWalletAdapter` opens LNURL-auth/pay/withdraw data for explicit user approval. Backend verification creates a Bitcoin or Lightning Principal. Device Binding and a short-lived PoP Session are still required for protected access: wallet proof or LNURL-auth alone is not authorization.

Install `WalletLnurlAuthProvider` with an application/platform signer that does not export its private key. The central transport signs protected calls using the production `Authorization: PoP` and `Bastion-Request-*` headers, canonical body/target, UTC timestamp, and a fresh cryptographic nonce. State is memory-only by default; core auth never persists to localStorage, sessionStorage, IndexedDB, cookies, or filesystem.

```ts
const auth = new WalletLnurlAuthProvider(deviceSigner);
const client = new BitcoinBastionClient({ baseUrl, auth, expectedLnurlAuthDomain: "auth.example.com" });
const intent = await client.walletAuth.createChallenge({
  action: "login", network: "bitcoin-mainnet", proofType: "bip322",
  origin: "https://app.example.com", deviceKeyFingerprint: deviceSigner.publicKeyFingerprint,
});
// Display canonicalIntent and safetyWarning before the user explicitly approves.
const proof = await externalWallet.signWalletIntent({ intent: intent.canonicalIntent, network: intent.network, action: "login" });
const login = await client.walletAuth.login({ challengeId: intent.challengeId, proof });
// Bind public device/session keys with createSession, then auth.setSession(backendSession).
```

LNURL wallet callbacks go directly to Bastion; the backend verifies k1, action, domain, expiry, replay, signature, revocation, settlement, entitlement, recovery, and policy. The SDK never treats invoice issuance as payment, comments/payerData as authorization or identity, Lightning Address as identity, or success-action URLs as automatic navigation. Authenticated WebSocket handshakes remain unsupported until the backend defines a secure ticket flow; secrets are never put in URLs.

### Migrating from Bearer API Key Authentication

Old `new BitcoinBastionClient({ baseUrl, apiKey })` usage fails closed. Temporary legacy transport requires the conspicuous `legacyBearerAuth: { enabled: true }` opt-in and does not authenticate Wallet/PoP protected endpoints. Migrate to `new BitcoinBastionClient({ baseUrl, auth: walletLnurlAuthProvider })`, establish external Wallet/LNURL proof, bind a Device Key, create a PoP Session, and handle structured policy/step-up/session-expiry errors. A transport retry must create a new signed attempt and therefore a new nonce and signature.
