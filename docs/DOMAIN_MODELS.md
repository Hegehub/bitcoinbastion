# Domain Models

Model list aligned to `app/db/models`.

## Auth
- `User`
- `SubscriptionPlan`
- `UserSubscription`

## News and reputation
- `BTCCandle`
- `IntelligenceTimelineEvent`
- `CandleProviderSnapshot`
- `CandleBuildRun`
- `BTCPricePoint`
- `ProviderHealthRecord`
- `MarketProviderHealth`
- `NewsEventArticle`
- `NewsEventCluster`
- `NewsSource`
- `NewsArticle`
- `SourceReputationProfile`
- `SourceHealthRecord`
- `NewsFetchLog`
- `NewsRawPayload`
- `NewsArticleCluster`
- `SourceHealthSnapshot`
- `ProviderConfidenceEvent`
- `NewsEvent`

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


## Bastion Trace
- `TraceReport`
- `TraceEvidence`
- `TraceSource`
- `TraceSourceSnapshot`
- `TraceWatchlistEntry`

## Labeling notes
- Some service-level outputs using these models are **BASELINE**.
- Citadel-dependent projections include **SYNTHETIC** elements in selected endpoints.


## RC lock note
- Domain model readiness is constrained by global quality gates; see `docs/FINAL_PRODUCTION_GAP_AUDIT.md`.


Bastion Trace status: INITIAL BASELINE / NOT PRODUCTION-COMPLETE
Advisory only; baseline scoring placeholder; no trusted external risk sources; no legal verdict; no consensus proof; no seed/private key intake; no Stratum/mining introduced.


Business Tier is a capability profile, not billing enforcement. Business policy actions are operational recommendations, not legal verdicts. Business policy actions do not execute payments. Batch screening accepts only public Bitcoin addresses. Sensitive wallet material is rejected and not stored. Review Desk is for operator review, not automated enforcement. Proof packets are evidence bundles, not legal certificates. API-key scopes are placeholders unless auth infrastructure exists. Bastion Trace: BUSINESS TIER BASELINE IMPLEMENTED / NOT PRODUCTION-CALIBRATED

Enterprise Tier is a capability profile, not billing enforcement. RBAC/SSO are placeholders unless connected to production auth/IdP. Legal Hold is operational metadata and not legal advice. Immutable Audit Log is append-only at application level unless WORM is configured. SIEM hooks are placeholders unless delivery infrastructure is configured. Retention auto-delete is disabled by default. Legal hold overrides retention. Enterprise proof packets are evidence bundles, not legal certificates. Bastion Trace: ENTERPRISE TIER GOVERNANCE BASELINE IMPLEMENTED / NOT PRODUCTION-CALIBRATED

Bastion Trace is a module inside Bitcoin Bastion, not the whole platform. Citadel consumes Trace as a separate advisory contribution. Policy Bridge does not execute payments. Treasury Bridge does not sign or broadcast transactions. Register Bridge is advisory and does not auto-reject payments. Cross-domain evidence refs preserve auditability. Trace production calibration is still pending. Bastion Trace: PLATFORM INTEGRATION BASELINE IMPLEMENTED / NOT PRODUCTION-CALIBRATED
Bastion Trace metrics use bounded labels only. Bitcoin addresses are never used as Prometheus labels. Trace status is operational and not a production calibration claim. Telegram commands are advisory and never request seed/private keys. Trace alerts are placeholders unless delivery infrastructure exists. Production alert delivery requires environment configuration. trace_production_calibrated remains false until real calibration evidence exists.


## Bastion Trace domain reference
See `docs/BASTION_TRACE_DOMAIN_MODEL.md` for Bastion Trace persistence and service-level artifact mapping.

- `NewsScore`: deterministic article/event scoring snapshot with factor breakdown and limitations.
- `NewsScore`
- `NewsArticleScore`

- `NewsNarrativeTag`
- `NewsPriceImpact`

- `ScoringFactor`
- `ScoreExplanation`

- `CandleAttribution`
- `AttributionReplayLog`
- `ImpactWindowSnapshot`
- `ImpactConfidenceBreakdown`

## Production Candle Attribution Models

- `CandleAttributionCandidate`: pre-ranking candidate evidence for candle attribution, including raw score, normalized score, ranking features, and rejection reason.
- `AttributionContextSnapshot`: replayable market/news context around a candle attribution run, including provider health, market regime, active news counts, and timeline snapshot data.
- `CandleAttributionCandidate`
- `AttributionContextSnapshot`
- `CandleContextSnapshot`

## Historical Similarity Models

- `HistoricalEventProfile`: normalized historical market-memory profile with pattern, narrative, sentiment, impact windows, confidence, and provider-confidence features.
- `HistoricalSimilarityResult`: persisted component-level similarity comparison with explanation JSON and limitations.
- `HistoricalEventProfile`
- `HistoricalSimilarityResult`

## Production Historical Similarity Models

- `HistoricalSimilarityRecord`: report-level historical analog evidence with component matches, reaction windows, confidence, and explanation JSON.
- `MarketPatternLibrary`: seeded deterministic market pattern taxonomy for ETF, regulatory, macro, security, miner, treasury, Lightning, and volatility narratives.
- `HistoricalSimilarityRecord`
- `MarketPatternLibrary`

## BMTM-30 Market Memory Models

- `MarketPattern`
- `EventPatternMatch`
- `HistoricalEventSimilarity`
- `PatternReactionProfile`

These models store the active production market-pattern catalog, ranked event pattern-classification evidence, replayable historical event similarities, and calibrated pattern reaction profiles.

## Historical Similarity Foundation Models

- `HistoricalPattern`
- `HistoricalSimilarityMatch`
- `HistoricalReactionProfile`

These models store the foundation pattern catalog, replayable event-to-event similarity component scores, and event-level BTC reaction profiles for evidence-based historical comparison.

## Narrative Heatmap Models

- `MarketNarrative`
- `NarrativeKeyword`
- `NarrativeSnapshot`

These models store the active Bitcoin narrative catalog, weighted deterministic keyword rules, and replayable narrative heatmap snapshots with confidence, provider state, evidence, and limitations.

## BMTM-033 Narrative Observation Model

- `NarrativeObservation`

This model stores article/event-level narrative classification observations with narrative type, observation score, confidence, source confidence, and observed time for replayable narrative intelligence.

### Task 34 Narrative Heatmap Fields

- `NarrativeObservation` includes `narrative_id`, `observation_time`, `strength_score`, and `relevance_score` for replayable classifier evidence.
- `NarrativeSnapshot` includes `velocity_score`, `dominance_score`, and `supporting_events_count` for leaderboard and heatmap rendering.

## BMTM-P35 Market Memory Engine Models

- `MarketMemoryRecord`
- `EventFingerprintRecord`
- `PatternStatistics`
- `MarketMemoryOperatorReview`

## BMTM-P36 Signal Governance Models

- `IntelligenceSignalCandidate`
- `IntelligenceOperatorReview`
- `IntelligencePublishingPolicy`
- `IntelligenceSignalDeliveryLog`

These models store governed candidate signals, operator review audit records, publication thresholds/defaults, and channel delivery outcomes.

## BMTM-P37 Evidence Packet and Replay Models
- `EvidencePacket`
- `EvidenceRelationship`
- `EvidenceArtifact`
- `EvidenceIntegritySnapshot`
- `EvidenceReplayLog`

These models persist replayable evidence bundles, lineage chains, artifact payloads, deterministic integrity snapshots, and replay logs for article, event, impact, attribution, signal, and publication evidence.


## Historical Similarity and Pattern Memory Models

- `market_patterns`: production pattern catalog with `pattern_code`, human name, category, default sentiment, default impact window, risk profile, confidence rules, active flag, and timestamps.
- `pattern_occurrences`: event/article/impact/attribution occurrence memory for a pattern.
- `historical_similarity_results`: source and candidate event comparisons with similarity, reaction similarity, confidence, and explanation JSON.
- `pattern_statistics`: occurrence counts, average/median moves across 15m/1h/4h/24h, success rate, and update timestamp.
- `pattern_reaction_snapshots`: immutable reaction snapshots per occurrence and reaction window.
- `market_narratives`: narrative memory fields for first seen, last seen, event count, average confidence, and related patterns.


### Model exports

- `PatternOccurrence`
- `PatternReactionSnapshot`
- `HistoricalReactionStatistics`
- `PatternEmbeddingPlaceholder`
- `NarrativeMemorySnapshot`

## Production observability models

- `SystemHealthSnapshot` stores rolled-up system health, degraded/critical counts, fallback state and operator-attention state.
- `ProviderHealthSnapshot` stores provider name/type, success/failure timestamps, failure counts, latency, confidence, backoff and health state.
- `BackgroundJobHealth` stores background job starts, finishes, durations, retry state, next schedule and worker name.
- `ServiceHealthSnapshot` stores service-level health snapshots for initialized runtime dependencies.
- `RuntimeStateSnapshot` stores system, provider, job, signal, evidence and Telegram runtime states.
- `DegradedComponentSnapshot` stores degraded component severity, recommendation, fallback usage and operator-attention flag.
- `RecoveryEvent` stores failure detection, fallback activation, restoration and operator-confirmation lifecycle details.

- `SystemHealthSnapshot`
- `ProviderHealthSnapshot`
- `BackgroundJobHealth`
- `ServiceHealthSnapshot`
- `RuntimeStateSnapshot`
- `DegradedComponentSnapshot`
- `RecoveryEvent`

## Operations control-plane models

- `OperationsEvidence` stores recovery drill evidence, operator notes, success status, and artifact references.
- `OperationsSLOSnapshot` stores SLO status for API availability, jobs, providers, signal latency, evidence latency, and replay latency.

- `OperationsEvidence`
- `OperationsSLOSnapshot`

## Disaster recovery validation models

- `BackupValidationRecord` stores backup ID, timestamps, success, checked objects, integrity verification and limitations.
- `RecoveryValidationRecord` stores restore/replay validation status, deterministic rebuild verification, integrity verification, replay types and limitations.

- `BackupValidationRecord`
- `RecoveryValidationRecord`
