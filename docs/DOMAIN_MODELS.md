# Domain Models

This is the canonical inventory of domain models exported by `app.db.models`.
The executable source of truth for membership in this inventory is
`app/db/models/__init__.py::__all__`; the referenced model modules and database
migrations remain the source of truth for fields, constraints, and persistence
semantics.

An exported model is part of the current Python package surface. Export does
not by itself mean that the feature is production-calibrated, externally
integrated, or enabled in every runtime profile. Current readiness and known
limitations are tracked in `docs/STATUS.md` and `docs/PRODUCTION_READINESS.md`.

## Access control and entitlements

Source: `app/db/models/access.py`.

- `AccessAuditEvent`
- `AccessCertificate`
- `AccessChallenge`
- `AccessDevice`
- `AccessPaymentIntent`
- `AccessRequestNonce`
- `AccessRevocation`
- `AccessSession`
- `ChildApiKey`
- `DelegatedPass`
- `MetricUsage`
- `RecoveryAttempt`
- `RecoveryQuorum`
- `SubscriptionEntitlement`

## Wallet authentication and recovery

Source: `app/db/models/wallet_auth.py`.

- `MultiWalletQuorum`
- `RecoveryCapsule`
- `WalletDevice`
- `WalletPrincipal`
- `WalletPrivacyCommitment`
- `WalletProof`
- `WalletSession`
- `WalletSessionNonce`
- `WalletStepUpProof`

## LNURL and Lightning identity

Source: `app/db/models/lnurl.py`.

- `LNURLAuthAttempt`
- `LNURLAuthChallenge`
- `LNURLInvoice`
- `LNURLPayRequest`
- `LNURLPayerData`
- `LNURLPaymentProof`
- `LNURLPrincipal`
- `LNURLReceiptPacket`
- `LNURLSuccessAction`
- `LNURLVerifyCheck`
- `LNURLWithdrawAttempt`
- `LNURLWithdrawRequest`
- `LightningAddress`
- `PayRegisterLNURLBinding`

## Storage and transactional outboxes

Sources: `app/db/models/storage_artifact.py`,
`app/db/models/storage_outbox_event.py`, and
`app/db/models/event_outbox.py`.

- `StorageArtifact`
- `StorageArtifactStatus`
- `StorageOutboxEvent`
- `StorageOutboxEventStatus`
- `EventOutbox`
- `EventOutboxStatus`

## Webhook management

Source: `app/db/models/webhooks.py`.

- `WebhookEndpoint`
- `WebhookEndpointStatus`
- `WebhookEventSubscription`
- `WebhookDelivery`
- `WebhookDeliveryStatus`

These exports cover endpoint configuration, subscriptions, and delivery
history. They do not by themselves prove that signed outbound delivery is
configured in a deployed environment.

## Market data and provider reliability

Sources: the corresponding modules under `app/db/models/`, including
`btc_candle.py`, `candle_build_run.py`, `candle_provider_snapshot.py`,
`btc_price_point.py`, `market_provider_health.py`, `mempool_fee_snapshot.py`,
`provider_health_record.py`, `provider_confidence_event.py`,
`source_health_record.py`, `source_health_snapshot.py`, and
`provider_source_health_timeseries.py`.

- `BTCCandle`
- `CandleBuildRun`
- `CandleProviderSnapshot`
- `BTCPricePoint`
- `MarketProviderHealth`
- `MempoolFeeSnapshot`
- `ProviderHealthRecord`
- `ProviderConfidenceEvent`
- `SourceHealthRecord`
- `SourceHealthSnapshot`
- `SourceConfidenceTimeSeriesEvent`
- `ProviderConfidenceTimeSeriesEvent`
- `SourceHealthTimeSeriesSnapshot`
- `ProviderHealthTimeSeriesSnapshot`

## Candle attribution and impact

Sources: the attribution, context, replay, and impact modules under
`app/db/models/`.

- `CandleAttribution`
- `CandleAttributionCandidate`
- `AttributionContextSnapshot`
- `CandleContextSnapshot`
- `AttributionReplayLog`
- `ImpactWindowSnapshot`
- `ImpactConfidenceBreakdown`

## Historical similarity and pattern memory

Sources: the historical similarity, pattern, reaction, market-memory, and
fingerprint modules under `app/db/models/`.

- `HistoricalEventProfile`
- `HistoricalSimilarityResult`
- `HistoricalSimilarityRecord`
- `MarketPatternLibrary`
- `PatternReactionProfile`
- `PatternOccurrence`
- `PatternReactionSnapshot`
- `HistoricalEventSimilarity`
- `EventPatternMatch`
- `MarketPattern`
- `MarketMemoryRecord`
- `EventFingerprintRecord`
- `PatternStatistics`
- `MarketMemoryOperatorReview`
- `HistoricalPattern`
- `HistoricalSimilarityMatch`
- `HistoricalReactionProfile`
- `HistoricalReactionStatistics`
- `PatternEmbeddingPlaceholder`

## Narrative memory

Sources: the narrative modules under `app/db/models/`.

- `MarketNarrative`
- `NarrativeKeyword`
- `NarrativeSnapshot`
- `NarrativeObservation`
- `NarrativeMemorySnapshot`
- `NewsNarrativeTag`

## News intelligence and scoring

Sources: the news, reputation, scoring, and price-impact modules under
`app/db/models/`.

- `NewsSource`
- `NewsArticle`
- `NewsArticleCluster`
- `SourceReputationProfile`
- `NewsEvent`
- `NewsEventArticle`
- `NewsEventCluster`
- `NewsFetchLog`
- `NewsRawPayload`
- `NewsScore`
- `NewsArticleScore`
- `NewsPriceImpact`
- `ScoringFactor`
- `ScoreExplanation`

## Signals, explainability, and evidence packets

Sources: `app/db/models/signal.py`, `app/db/models/signal_link.py`,
`app/db/models/explainability.py`, `app/db/models/evidence_packet.py`,
`app/db/models/intelligence_timeline.py`, and
`app/db/models/intelligence_signals.py`.

- `Signal`
- `SignalSourceLink`
- `SignalExplanation`
- `EvidenceNode`
- `EvidenceEdge`
- `EvidencePacket`
- `EvidenceRelationship`
- `EvidenceArtifact`
- `EvidenceIntegritySnapshot`
- `EvidenceReplayLog`
- `IntelligenceTimelineEvent`
- `IntelligenceSignalCandidate`
- `IntelligenceOperatorReview`
- `IntelligencePublishingPolicy`
- `IntelligenceSignalDeliveryLog`

## Runtime health and recovery evidence

Sources: `app/db/models/observability_health.py` and
`app/db/models/operations_control.py`.

- `SystemHealthSnapshot`
- `ProviderHealthSnapshot`
- `BackgroundJobHealth`
- `ServiceHealthSnapshot`
- `RuntimeStateSnapshot`
- `DegradedComponentSnapshot`
- `RecoveryEvent`
- `OperationsEvidence`
- `OperationsSLOSnapshot`
- `BackupValidationRecord`
- `RecoveryValidationRecord`

## Operational records and delivery

Sources: `app/db/models/audit.py`, `app/db/models/job_run.py`,
`app/db/models/metric_usage_event.py`, `app/db/models/delivery.py`, and
`app/db/models/telegram.py`.

- `AuditLog`
- `JobRun`
- `MetricUsageEvent`
- `DeliveryLog`
- `TelegramDeliveryLog`

## Users and subscriptions

Source: `app/db/models/auth.py`.

- `User`
- `SubscriptionPlan`
- `UserSubscription`

## Entities and on-chain observations

Sources: `app/db/models/entity.py`, `app/db/models/watched_entity.py`, and
`app/db/models/onchain.py`.

- `Entity`
- `EntityAddress`
- `WatchedEntity`
- `OnchainEvent`

## Wallet profile and health

Source: `app/db/models/wallet.py`.

- `WalletProfile`
- `WalletHealthReport`

## Treasury and policy runtime

Source: `app/db/models/treasury.py`.

- `TreasuryRequest`
- `PsbtWorkflow`
- `TreasuryPolicy`
- `PolicyRule`
- `PolicyExecutionLog`

Treasury models support advisory and policy workflows; they do not sign or
broadcast transactions.

## Bastion Trace

Source: `app/db/models/bastion_trace.py`. Persistence and service-level
artifact mapping are described in `docs/BASTION_TRACE_DOMAIN_MODEL.md`.

- `TraceReport`
- `TraceEvidence`
- `TraceSource`
- `TraceSourceSnapshot`
- `TraceWatchlistEntry`

Bastion Trace remains advisory and is not a legal verdict or consensus proof.
Its current calibration status is documented in `docs/STATUS.md`.

## Citadel

Source: `app/db/models/citadel_assessment.py`.

- `CitadelAssessment`

Citadel projections may include synthetic elements where explicitly identified
by the relevant API response and status documentation.
