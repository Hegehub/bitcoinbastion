# Bitcoin Bastion Python SDK

SDK status: developer preview.

The Python SDK is a typed client for the Bitcoin Bastion Developer/API layer. It wraps existing backend endpoints for Trace, signals, news, on-chain state, evidence, market intelligence context, treasury review workflows, policy checks, wallet health metadata, provider health, webhooks, and WebSocket event subscriptions.

Bitcoin Bastion is no-custody. Never submit seed phrases, private keys, wallet files, xprv/yprv/zprv, or signing material. Trace outputs are advisory-only. Trace is not legal verification. Trace is not Bitcoin consensus proof. Market intelligence is not financial advice. Historical similarity does not guarantee future market behavior.

## Installation

```bash
cd sdk/python
python -m pip install -e '.[dev]'
```

## Quickstart

```python
from bitcoin_bastion_sdk import BastionClient

client = BastionClient(base_url="http://localhost:8000")
summary = client.trace.get_public_summary(1)
print(summary)
```

## Async client

```python
from bitcoin_bastion_sdk import AsyncBastionClient

async with AsyncBastionClient(base_url="http://localhost:8000") as client:
    latest = await client.signals.latest()
```

## Wallet-first and LNURL authentication

**Never provide Bitcoin Bastion with your Bitcoin wallet seed or private key.** Use a
dedicated Bastion authentication wallet/address for routine authentication when possible;
do not use a cold treasury wallet for routine login.

The SDK constructs structured intents and submits externally produced BIP-322 proofs. It
does not derive wallet keys, sign Bitcoin transactions, or broadcast transactions:

```python
intent = client.auth.wallet.create_challenge(
    action="login",
    network="bitcoin-mainnet",
    proof_type="bip322",
    origin="https://bastion.example",
)
print(intent.signable_intent)  # sign with an external wallet
# client.auth.wallet.login(challenge_id=intent.challenge_id, signature=external_signature, ...)
```

LNURL-auth returns a QR/deep-link for an external Lightning wallet. LNURL-auth proves
control of a domain-specific Lightning linking key; it is not on-chain ownership proof and
does not itself grant protected API access.

```python
flow = client.auth.lnurl.create_auth_challenge(action="login", origin="https://bastion.example")
print(flow.lnurl)
```

### Device Key and PoP Session

Wallet/LNURL v2 protected calls use a caller-controlled `DeviceSigner` and in-memory
`BastionPoPSession`. The shared transport signs each request using
`Authorization: PoP sess_...` and `Bastion-Request-*`; every attempt receives a fresh
cryptographic nonce. The SDK does not persist sessions automatically. The included
`InMemoryDeviceSigner` is for development/testing, not an OS keychain, TPM, Secure Enclave,
or hardware-wallet integration.

### LNURL-pay and verification

```python
payment = client.auth.lnurl.create_subscription_payment(plan="pro_pass")
print(payment.lnurl)
status = client.auth.lnurl.verify_payment(payment.payment_id)
if status.settled and status.entitlement_active:
    print("settlement verified and entitlement active")
```

Invoice issuance is not settlement. Lightning Address is payment routing, not identity.
Comments are untrusted metadata, payer email/name are never auto-populated, and
`successAction` URLs are validated but never opened automatically.

### Step-up, recovery, lockdown, and certificates

Use `client.auth.wallet.step_up(...)` or `client.auth.lnurl.step_up(...)` for backend-required
Human Intent approval. Recovery methods actively reject seed, mnemonic, xprv, WIF, and
private-key fields. `client.auth.lockdown` and `client.auth.recovery` expose the implemented
Wallet Auth routes. Optional Access Certificates remain non-bearer policy inputs; local
`.bbp` writing uses exclusive creation and restrictive permissions.

### Self-hosted and Onion deployments

HTTPS is required for normal remote deployments. Local HTTP is limited to loopback
development; self-hosted mode must be explicit. Onion endpoints require `allow_onion=True`
and a caller-configured Tor-capable HTTP transport—the SDK does not silently proxy traffic.

## Legacy Access v1 compatibility

Existing Access Certificate resources may temporarily use `BastionAccessAuth` and
`X-Bastion-*`. Wallet/LNURL v2 uses only canonical PoP headers. No flow falls back to Bearer,
password, or JWT authentication.

```python
from datetime import UTC, datetime, timedelta

from bitcoin_bastion_sdk import BastionAccessAuth, BastionClient
from bitcoin_bastion_sdk.access_auth import AccessSession
from bitcoin_bastion_sdk.signing import InMemoryDeviceSigner

signer = InMemoryDeviceSigner(b"replace-with-vault-backed-bastion-device-secret")
session = AccessSession(
    session_token="session-token-from-/access/sessions",
    expires_at=datetime.now(UTC) + timedelta(minutes=15),
    scopes=["market:intelligence:read"],
    plan_code="pro_pass",
)
client = BastionClient(
    base_url="https://bastion.example",
    access_auth=BastionAccessAuth.from_session(session, signer=signer),
)
me = client.access.me()
```

Legacy `api_key`/`Authorization: Bearer` authentication is disabled. The compatibility
argument is rejected and never sends credentials. Removal of Access v1 aliases is planned
after the SDK migration window.

## Trace example

```python
report = client.trace.analyze_address("bc1qexamplepublicaddress000000000000000000000")
evidence = client.trace.get_evidence(report["report_id"])
packet = client.trace.get_proof_packet(report["report_id"])
```

Trace payloads preserve limitations, confidence, source quality, freshness, evidence references, operator guidance, `no_custody`, `not_consensus_proof`, and advisory fields when the backend provides them.

## Signals example

```python
signals = client.signals.latest()
for signal in signals:
    print(signal.get("confidence"), signal.get("limitations"))
```

Signals are not financial advice and must preserve correlation-not-causation and operator-review context.

## Evidence example

```python
packet = client.evidence.get_packet("packet-123")
replay = client.evidence.get_replay("trace_report", 55)
```

Evidence endpoints are application-level evidence summaries and replay metadata, not legal verification.

## Webhook creation

```python
webhook = client.webhooks.create(
    url="https://example.com/bastion-webhook",
    events=["signal.published", "trace.report.created", "provider.degraded"],
)
```

Webhooks are notification channels only. They do not authorize transaction execution or custody actions.

## Webhook signature verification

```python
from bitcoin_bastion_sdk.webhooks import verify_signature

valid = verify_signature(
    payload=raw_body,
    secret="whsec_test_...",
    timestamp=headers["X-Bastion-Timestamp"],
    signature=headers["X-Bastion-Signature"],
)
```

Verification uses HMAC SHA256, constant-time comparison, and timestamp tolerance.

## WebSocket subscriptions

```python
async with client.websocket.subscribe_events(topics=["signals", "trace"]) as stream:
    async for event in stream:
        print(event["event_type"], event.get("payload"))
```

Specialized streams are available through:

```python
async for event in client.websocket.subscribe("provider-health"):
    print(event)
```

Supported streams: `signals`, `news`, `onchain`, `market`, `trace`, `treasury`, `provider-health`, and `intelligence-timeline`.

## Implemented resources

- `client.signals.list_top()`, `latest()`, `get()`, `get_evidence()`, `get_delivery_logs()`, `recommendations()`, `explanation()`
- `client.news.latest()`, `events()`, `get_event()`, `article_score()`
- `client.onchain.events()`, `state()`
- `client.trace.lite()`, `analyze_address()`, `get_report()`, `get_public_summary()`, `get_evidence()`, `get_proof_packet()`, `get_privacy_shield()`, `get_origin_passport()`, `get_counterparty_lens()`, `get_policy_facts()`, `source_summary()`, `provider_disagreement()`, `utxo_hygiene()`, `dust_radar()`, `batch()`, `treasury_destination_check()`
- `client.evidence.list_packets()`, `get_packet()`, `get_replay()`, `market_memory()`
- `client.market.dashboard()`, `timeline()`, `time_machine()`, `signals()`, `narratives()`, `sources()`, `provider_health()`, `candle_evidence()`
- `client.treasury.create_request()`, `list_requests()`, `pending_approvals()`, `approve_request()`, `reject_request()`
- `client.policy.evaluate()`, `list_profiles()`, `executions()`
- `client.wallet.health()`, `profile_health()`, `profiles()`
- `client.provider_health.list()`, `get()`, `degraded()`
- `client.webhooks.create()`, `list()`, `get()`, `update()`, `delete()`, `test()`, `deliveries()`

## Planned endpoints not enabled in SDK yet

These concepts are documented but not exposed as SDK methods until backend endpoints exist:

- News `get_article(article_id)` full article retrieval.
- Evidence `export_json(packet_id)` and `export_markdown(packet_id)` export endpoints.
- Policy `get_profile(profile_id)` by id.
- Wallet `privacy_risk(wallet_id)` endpoint.
- Provider health direct `GET /provider/{name}` endpoint; `get()` currently filters the existing provider list response.
- On-chain convenience methods for large transfers and fee spikes beyond the existing event list endpoint.

## Safety

The SDK rejects user-supplied values that appear to contain seed phrases, mnemonics, private keys, wallet files, xprv/yprv/zprv values, or signing material. Public Bitcoin addresses and public/internal identifiers are allowed.
