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


## Mining sovereignty (MODELS/PERSISTENCE BASELINE IMPLEMENTED)
Persistence models now present in `app/db/models/mining.py`:
- `MiningPool` → canonical pool identity + source-quality and confidence metadata.
- `MiningPoolEndpoint` → pool endpoint inventory and endpoint-level quality/freshness context.
- `StratumV2Capability` → SV2/JD/translator/encryption capability state snapshots (unknown/unverified-safe).
- `PoolSovereigntyScore` → deterministic sovereignty score snapshots with explainability payload references.
- `MiningCensorshipRisk` → deterministic censorship-risk snapshots with risk level + factor payload references.
- `TemplateControlAssessment` → template control owner/state and interference/MITM semantics snapshots.
- `MiningSignal` → mining-domain signal records for advisory downstream consumption.

Table-purpose notes:
- These tables implement persistence baseline only; they do not imply fully implemented provider ingestion or production-grade mining analytics runtime.
- Source-quality semantics are persisted through `source_type`, `is_verified`, `is_fallback`, `is_synthetic`, `confidence_score`, freshness/observed timestamps, limitations, and evidence refs.
- Unknown/unverified handling is first-class: capability and severity/risk state fields default to `unknown` and verification defaults to false.

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
