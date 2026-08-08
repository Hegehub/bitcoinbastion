# Documentation Index

Lifecycle: **ACTIVE**
Last reviewed: **2026-07-15**

This index points to the canonical documentation for each topic. Documents under
`archive/` preserve historical evidence and generation context; they are not
current implementation or readiness guidance.

## Start here

- [Current repository status](STATUS.md)
- [Repository layout](REPOSITORY_LAYOUT.md)
- [Production readiness contract](PRODUCTION_READINESS.md)
- [Roadmap](ROADMAP.md)
- [Architecture](ARCHITECTURE.md)
- [Known limitations](KNOWN_LIMITATIONS.md)
- [Technical debt](TECHNICAL_DEBT.md)

## Access and wallet security

- [Proof-of-Access overview](ACCESS_LAYER.md)
- [Access API](API_ACCESS.md)
- [Request signing](ACCESS_REQUEST_SIGNING.md)
- [Recovery](ACCESS_RECOVERY.md)
- [Wallet-first/LNURL ADR](ADR_WALLET_FIRST_LNURL_PROOF_OF_ACCESS_AUTH.md)
- [Wallet/LNURL threat model](WALLET_FIRST_LNURL_THREAT_MODEL.md)
- [Wallet authentication security](WALLET_AUTH_SECURITY.md)

## API and developer interfaces

- [API contracts](API_CONTRACTS.md)
- [Domain models](DOMAIN_MODELS.md)
- [Public API](PUBLIC_API.md)
- [Python SDKs](SDK.md)
- [TypeScript SDK](TYPESCRIPT_SDK.md)
- [CLI](CLI.md)
- [MCP connector](MCP_CONNECTOR.md)
- [Plugin API](PLUGIN_API.md)

## Market intelligence and evidence

- [Market Time Machine](MARKET_TIME_MACHINE.md)
- [Candle attribution](CANDLE_ATTRIBUTION.md)
- [Historical similarity](HISTORICAL_SIMILARITY_ENGINE.md)
- [Narrative heatmap](NARRATIVE_HEATMAP_ENGINE.md)
- [Market signal governance](MARKET_SIGNAL_GOVERNANCE.md)
- [Evidence packets](EVIDENCE_PACKETS.md)
- [Evidence replay](EVIDENCE_REPLAY.md)

## Trace and Citadel

- [Bastion Trace](BASTION_TRACE.md)
- [Trace API](BASTION_TRACE_API.md)
- [Trace report UI](TRACE_REPORT_UI.md)
- [Citadel specification](SPEC_CITADEL.md)
- [Synthetic risk register](CITADEL_SYNTHETIC_RISK_REGISTER.md)

## Frontend

- [Frontend migration Prompt 0/25 baseline](frontend/migration/00_BASELINE_AUDIT.md)
- [Prompt 1/25 contract-foundation blockers](frontend/migration/01_CONTRACT_FOUNDATION_BLOCKERS.md)
- [Canonical frontend execution plan 0–25](frontend/migration/00_EXECUTION_PLAN_0_25.md)
- [Approved reconciled 69-feature register](frontend/migration/00_69_FEATURE_REGISTER.md)

- [Reflex frontend](REFLEX_FRONTEND.md)
- [Reflex testing](FRONTEND_REFLEX_TESTING.md)
- [Route/API parity contract](FRONTEND_REFLEX_API_PARITY.md)
- [UI/UX and safety principles](UI_UX_PRINCIPLES.md)
- [Accessibility baseline](../frontend/docs/ACCESSIBILITY.md)
- [Design system](../frontend/docs/DESIGN_SYSTEM.md)

## Storage, operations, and deployment

- [Deployment methods: choose, run, and verify](DEPLOYMENT_METHODS.md)
- [Storage architecture](STORAGE_LAYER_ARCHITECTURE.md)
- [Storage backup and recovery](STORAGE_BACKUP_RECOVERY.md)
- [Disaster recovery](DISASTER_RECOVERY.md)
- [Operations runbook](OPERATIONS_RUNBOOK.md)
- [Runbook index](RUNBOOKS.md)
- [Runtime profile metadata contract](RUNTIME_PROFILES.md)
- [Kubernetes deployment](KUBERNETES.md)
- [Deployment evidence pack](DEPLOYMENT_EVIDENCE_PACK.md)
- [Release candidate gates](RELEASE_CANDIDATE_GATES.md)

## Security

- [Security overview](SECURITY.md)
- [Security hardening](SECURITY_HARDENING.md)
- [Public API security](PUBLIC_API_SECURITY.md)
- [Secrets management](SECRETS_MANAGEMENT.md)
- [Supply-chain security](SUPPLY_CHAIN_SECURITY.md)
- [Incident response](INCIDENT_RESPONSE.md)

## Historical material

- [Archive index](archive/README.md)
- [Prompt 1A contract-authority stop report](frontend/migration/01A_CONTRACT_AUTHORITY_STOP_REPORT.md) — unresolved source-authority gates before Prompt 1B.
