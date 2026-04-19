# Domain Models

Below is the current implemented model baseline aligned to `app/db/models`.

## Auth
- `User`
- `SubscriptionPlan`
- `UserSubscription`

## News & reputation
- `NewsSource`
- `NewsArticle`
- `SourceReputationProfile`

## Entities
- `Entity`
- `EntityAddress`
- `WatchedEntity`

## On-chain
- `OnchainEvent`

## Signals & explainability
- `Signal`
- `SignalSourceLink`
- `SignalExplanation`
- `EvidenceNode`
- `EvidenceEdge`

## Wallet / sovereignty baseline
- `WalletProfile`
- `WalletHealthReport`

## Treasury & policy runtime
- `TreasuryRequest`
- `PsbtWorkflow`
- `TreasuryPolicy`
- `PolicyRule`
- `PolicyExecutionLog`

## Delivery / audit / operations
- `DeliveryLog`
- `TelegramDeliveryLog`
- `AuditLog`
- `JobRun`

## Notes
- The model graph already supports first-level explainability and policy execution traceability.
- Future iterations should extend provenance depth, sovereignty graph snapshots, and richer privacy telemetry.
