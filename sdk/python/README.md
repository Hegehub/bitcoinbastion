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

client = BastionClient(base_url="http://localhost:8000", api_key="optional-token")
summary = client.trace.get_public_summary(1)
print(summary)
```

## Async client

```python
from bitcoin_bastion_sdk import AsyncBastionClient

async with AsyncBastionClient(base_url="http://localhost:8000") as client:
    latest = await client.signals.latest()
```

## Auth

```python
client = BastionClient(
    base_url="https://bastion.example",
    api_key="token",
    headers={"X-Custom": "value"},
)
```

The SDK sends `Authorization: Bearer <token>` and does not include tokens in exception messages.

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
