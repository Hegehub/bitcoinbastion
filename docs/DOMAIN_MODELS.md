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
