# Domain Models

Model list aligned to `app/db/models`.

## Auth
- `User`
- `SubscriptionPlan`
- `UserSubscription`

## News and reputation
- `NewsSource`
- `NewsArticle`
- `SourceReputationProfile`

## Entities
- `Entity`
- `EntityAddress`
- `WatchedEntity`

## On-chain
- `OnchainEvent`

## Signals and explainability
- `Signal`
- `SignalSourceLink`
- `SignalExplanation`
- `EvidenceNode`
- `EvidenceEdge`

## Citadel
- `CitadelAssessment`

## Wallet
- `WalletProfile`
- `WalletHealthReport`

## Mining sovereignty (M0 draft, persistence not yet introduced)
- `MiningWindow`
- `HashrateSnapshot`
- `PoolShareSnapshot`
- `BlockProductionSnapshot`
- `InclusionCensorshipSnapshot`
- `MiningExplainabilityNode`
- `MiningSovereigntyScorecard`


## Treasury and policy runtime
- `TreasuryRequest`
- `PsbtWorkflow`
- `TreasuryPolicy`
- `PolicyRule`
- `PolicyExecutionLog`

## Delivery and operations
- `DeliveryLog`
- `TelegramDeliveryLog`
- `AuditLog`
- `JobRun`

## Labeling notes
- Some service-level outputs using these models are **BASELINE**.
- Citadel-dependent projections include **SYNTHETIC** elements in selected endpoints.
