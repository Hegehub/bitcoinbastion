# Bitcoin Observation Model

## Current blockchain source inventory

The repository currently has these blockchain data sources:

- `app.integrations.bitcoin.provider.BitcoinProvider`, with `EsploraProvider` when `bitcoin_esplora_url` is configured and `MockBitcoinProvider` as a degraded/fallback local runtime source.
- `app.db.models.onchain.OnchainEvent` and `OnchainRepository`, which persist normalized on-chain events used by `/api/v1/onchain/events`, `/api/v1/onchain/state`, signal generation, operations health, and provider health.
- Mempool, UTXO, fee, wallet, and Citadel services consume runtime-provided or fallback values, but they do not currently provide authoritative transaction topology observations.

No external SaaS provider or new blockchain provider is introduced by the observation model.

## Observation architecture

A Bitcoin observation is the smallest immutable factual blockchain statement emitted by backend analysis. It is not a relationship, graph node, graph edge, report, projection, cluster, risk score, ownership statement, counterparty inference, or UI concern.

## Observation type hierarchy

Only observation types currently producible from `ChainEvent` / `OnchainEvent` are defined:

- `TransactionObserved`: a transaction reference and observed value.
- `AddressObserved`: an address string appearing in the current event record.
- `FeeObserved`: fee value when an event authoritatively carries `fee_sats`.
- `ConfirmationObserved`: block-height observation when an event carries a positive block height.

Input/output/spend/UTXO/block/script observations are intentionally deferred until repository sources emit those facts directly.

## Producer architecture

`BitcoinObservationProducer` is the canonical backend producer for Bitcoin observations. It can project immutable observations from an existing `OnchainEvent` or persist a `ChainEvent` through `OnchainRepository` before emitting observations. It normalizes values, assigns deterministic identities, preserves provenance, and never creates relationships.

## Identity strategy

Observation IDs are SHA-256 based stable IDs over observation version, observation type, and canonical factual parts. Equivalent observations resolve to the same identity. Corrections produce new observations because factual parts change.

## Version strategy

`bitcoin-observation-v1` is independent from Graph version, Snapshot version, API version, and DTO schema version.

## Provenance strategy

Every observation carries producer name, source metadata, RPC/indexer origin when known, collection method, and limitations. The base limitations include `observation_only`, `no_relationships`, and `no_interpretation`.

## Persistence decisions

Canonical persistence reuses existing `OnchainEvent` storage through `OnchainRepository`. The new observation layer does not create duplicate tables. Immutable observation objects are deterministic projections from persisted on-chain events. If future prompts require durable observation rows, that migration must preserve `OnchainEvent` compatibility and avoid duplicate sources of truth.

## Boundaries

The observation layer does not infer clusters, ownership, counterparties, behavior, risk, intent, identity, flow, or relationships. T2 is responsible for topology production from these observations.

## Rollback

Rollback can remove `app/services/bitcoin_observations/`, the ingestion integration line, this document, and observation tests. Graph Domain, Graph Builder, snapshots, history, reports, APIs, persistence, and user data remain intact.
