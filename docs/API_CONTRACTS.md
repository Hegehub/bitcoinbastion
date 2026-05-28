# API Contracts

## Base conventions
- API prefix: `/api/v1`
- Most business endpoints return `ResponseEnvelope[T]`
- List endpoints use `PaginatedData`
- Error envelope shape: `{"success": false, "error": {"code": "...", "message": "...", "request_id": "..."}}`

## Compatibility lock (P6-09)
- Response envelope contract for non-exception endpoints is locked to:
  - success path: `{"success": true, "data": ...}`
  - error path: `{"success": false, "error": {"code", "message", "request_id"}}`
- Paginated route contract is locked to:
  - `{"success": true, "data": {"items": [...], "total": <int>, "limit": <int>, "offset": <int>}}`
- Backward compatibility rule: envelope shape changes are disallowed unless explicitly versioned and announced in release notes.

## Envelope exceptions (implemented)
- `GET /api/v1/health`
- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`

These endpoints intentionally return direct schema payloads (not `ResponseEnvelope`).

## Implemented route inventory

### Health and observability
- `GET /api/v1/health`
- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`
- `GET /api/v1/observability/snapshot`
- `GET /metrics`

### Auth and users
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/users`
- `GET /api/v1/users/me`

### News
- `GET /api/v1/news/latest`
- `GET /api/v1/news/sources`
- `GET /api/v1/news/sources/tiers`
- `GET /api/v1/news/sources/{source_id}/confidence-events`
- `GET /api/v1/news/sources/{source_id}/snapshots`
- `GET /api/v1/news/sources/{source_id}/health`
- `GET /api/v1/news/sources/health`
- `GET /api/v1/news/sources/categories`
- `GET /api/v1/news/sources/{source_id}`
- `POST /api/v1/news/sources/reputation/refresh`
- `GET /api/v1/news/sources/reputation`

### Signals, entities, on-chain
- `GET /api/v1/signals/top`
- `GET /api/v1/signals/{signal_id}/recommendations`
- `GET /api/v1/signals/{signal_id}/explanation`
- `GET /api/v1/entities`
- `GET /api/v1/entities/watchlist`
- `POST /api/v1/entities/provenance/refresh`
- `GET /api/v1/onchain/events`
- `GET /api/v1/onchain/state`

### Wallet, fees, privacy, treasury
- `POST /api/v1/wallet/health`
- `POST /api/v1/wallet/profiles/{wallet_profile_id}/health`
- `GET /api/v1/wallet/profiles/{wallet_profile_id}/health/reports`
- `GET /api/v1/wallet/profiles`
- `POST /api/v1/fees/recommendation`
- `POST /api/v1/privacy/assess`
- `POST /api/v1/treasury/requests`
- `POST /api/v1/treasury/requests/{request_id}/approve`
- `POST /api/v1/treasury/requests/{request_id}/reject`
- `GET /api/v1/treasury/requests/pending-approvals`
- `GET /api/v1/treasury/requests`

### Policy and education
- `POST /api/v1/policy/check`
- `POST /api/v1/policy/simulate`
- `GET /api/v1/policy/executions`
- `GET /api/v1/policy/executions/summary`
- `POST /api/v1/policy/catalog`
- `POST /api/v1/policy/catalog/compare`
- `GET /api/v1/policy/catalog`
- `GET /api/v1/education/snippets`

### Citadel
- `GET /api/v1/citadel/overview`
- `GET /api/v1/citadel/assessment`
- `POST /api/v1/citadel/recalculate`
- `GET /api/v1/citadel/dependencies`
- `GET /api/v1/citadel/recovery`
- `POST /api/v1/citadel/simulations`
- `GET /api/v1/citadel/simulations`
- `GET /api/v1/citadel/inheritance`
- `GET /api/v1/citadel/repair-plan`
- `GET /api/v1/citadel/policy-checks`

### Bastion Trace
- `GET /api/v1/trace/address/{address}`
- `GET /api/v1/trace/report/{report_id}`
- `GET /api/v1/trace/report/{report_id}/evidence`
- `GET /api/v1/trace/sources`
- `GET /api/v1/trace/watchlist`
- `POST /api/v1/trace/watchlist`

- `GET /api/v1/trace/report/{report_id}/origin-passport`
- `GET /api/v1/trace/report/{report_id}/source-summary`
- `GET /api/v1/trace/report/{report_id}/provider-disagreement`
- `GET /api/v1/trace/sources/{source_name}`
- `GET /api/v1/trace/report/{report_id}/privacy-shield`
- `GET /api/v1/trace/report/{report_id}/utxo-hygiene`
- `GET /api/v1/trace/report/{report_id}/dust-radar`
- `GET /api/v1/trace/report/{report_id}/counterparty-lens`
- `POST /api/v1/trace/payment-context`
- `POST /api/v1/trace/payment-intent/preview`
- `POST /api/v1/trace/destination-review`
- `GET /api/v1/trace/lite/{address}`
### Admin
- `GET /api/v1/admin/status`
- `GET /api/v1/admin/jobs`
- `GET /api/v1/admin/jobs/runs`
- `GET /api/v1/admin/audit-logs`
- `GET /api/v1/admin/jobs/recovery-check`
- `POST /api/v1/admin/jobs/retry`

## Observability snapshot contract notes (implemented)
`GET /api/v1/observability/snapshot` includes:
- `runtime_severity`: deterministic severity score/level, escalation conditions, operator guidance.
- `degraded_mode`: explicit degraded-runtime marker, degraded reasons, component states, confidence penalty.
- `operational_evidence`: compact operational audit packet with runtime state, degraded dependencies, provider quality, unresolved findings, delivery health, drill status, and recovery SLO status.

These fields are operational governance aids and not guarantees of external SLO attainment.

## Protocol source-quality fields (implemented)
- `GET /api/v1/onchain/state` includes source-quality metadata in `freshness` and `explainability` (including fallback/mock semantics when applicable).
- Citadel explainability includes `input_quality` and `protocol_input_quality` domains to expose protocol data maturity and fallback/synthetic limitations.
- Mempool/UTXO service-driven outputs include source-quality/freshness limitations in explainability fields; these are advisory and conservative.

### On-chain state data source compatibility
`GET /api/v1/onchain/state` `data.explainability.data_source` may intentionally be one of:
- `query`
- `repository_fallback`
- `provider_probe`
- `provider_fallback`

Clients should treat these as source-quality markers and avoid strict assumptions on a single fallback string.

## Backward compatibility notes
- Envelope exceptions are explicit and stable unless versioned.
- Pagination fields (`items`, `total`, `limit`, `offset`) are required for paginated endpoints.
- Error envelope shape is standardized across auth/validation/http/application errors.


## RC lock note
- RC promotion remains blocked until quality gates in `docs/FINAL_PRODUCTION_GAP_AUDIT.md` are closed.


## Bastion Trace
Bastion Trace status: INITIAL BASELINE / NOT PRODUCTION-COMPLETE
Advisory only; baseline scoring placeholder; no trusted external risk sources; no legal verdict; no consensus proof; no seed/private key intake; no Stratum/mining introduced.


Trace address responses include `trace_dna`, `factor_contributions`, `confidence_ledger`, `score_breakdown`, and deterministic baseline reason codes.


Bastion Trace: BASELINE SCORING + EVIDENCE RECEIPTS + ORIGIN/SOURCE BASELINE IMPLEMENTED / NOT PRODUCTION-CALIBRATED

Business Tier is a capability profile, not billing enforcement. Business policy actions are operational recommendations, not legal verdicts. Business policy actions do not execute payments. Batch screening accepts only public Bitcoin addresses. Sensitive wallet material is rejected and not stored. Review Desk is for operator review, not automated enforcement. Proof packets are evidence bundles, not legal certificates. API-key scopes are placeholders unless auth infrastructure exists. Bastion Trace: BUSINESS TIER BASELINE IMPLEMENTED / NOT PRODUCTION-CALIBRATED

Enterprise Tier is a capability profile, not billing enforcement. RBAC/SSO are placeholders unless connected to production auth/IdP. Legal Hold is operational metadata and not legal advice. Immutable Audit Log is append-only at application level unless WORM is configured. SIEM hooks are placeholders unless delivery infrastructure is configured. Retention auto-delete is disabled by default. Legal hold overrides retention. Enterprise proof packets are evidence bundles, not legal certificates. Bastion Trace: ENTERPRISE TIER GOVERNANCE BASELINE IMPLEMENTED / NOT PRODUCTION-CALIBRATED

Bastion Trace is a module inside Bitcoin Bastion, not the whole platform. Citadel consumes Trace as a separate advisory contribution. Policy Bridge does not execute payments. Treasury Bridge does not sign or broadcast transactions. Register Bridge is advisory and does not auto-reject payments. Cross-domain evidence refs preserve auditability. Trace production calibration is still pending. Bastion Trace: PLATFORM INTEGRATION BASELINE IMPLEMENTED / NOT PRODUCTION-CALIBRATED
Bastion Trace metrics use bounded labels only. Bitcoin addresses are never used as Prometheus labels. Trace status is operational and not a production calibration claim. Telegram commands are advisory and never request seed/private keys. Trace alerts are placeholders unless delivery infrastructure exists. Production alert delivery requires environment configuration. trace_production_calibrated remains false until real calibration evidence exists.


## Bastion Trace contract reference
See `docs/BASTION_TRACE_API.md` for route-level Bastion Trace status (implemented/baseline/placeholder), safety notes, and explicit not-implemented routes.


## Public presentation APIs
- `GET /api/v1/public/landing`
- `GET /api/v1/public/status`
- `GET /api/v1/public/roadmap`
- `GET /api/v1/public/stats`
- `GET /api/v1/public/features`
- `GET /api/v1/public/trace/{report_id}/summary`


## API Envelope and Errors
- Current envelope baseline: success/data for success responses; standardized `error` payload for failures from global handlers.
- Stable error code targets: invalid_bitcoin_address, sensitive_wallet_material_not_accepted, report_not_found, proof_packet_not_found, unsupported_export_format, feature_placeholder, insufficient_evidence, rate_limited, backend_unavailable, validation_error, internal_error.
- API versioning: `/api/v1` with backward-compatible additive changes preferred.

- `GET /api/v1/news/clusters`
- `GET /api/v1/news/clusters/{cluster_id}`
- `GET /api/v1/news/articles/{article_id}/duplicates`

### News Events API
- GET /api/v1/news/events
- GET /api/v1/news/events/{event_id}
- GET /api/v1/news/events/{event_id}/articles
- GET /api/v1/news/events/high-impact
- GET /api/v1/news/events/security
- GET /api/v1/news/events/regulatory


- `GET /api/v1/news/events`
- `GET /api/v1/news/events/{event_id}`
- `GET /api/v1/news/events/{event_id}/articles`
- `GET /api/v1/news/events/high-impact`
- `GET /api/v1/news/events/security`
- `GET /api/v1/news/events/regulatory`
- `GET /api/v1/market/btc/price`
- `GET /api/v1/market/btc/providers`
- `GET /api/v1/market/btc/providers/health`
- `GET /api/v1/market/btc/price/history`

- `GET /api/v1/market/btc/context`
- `GET /api/v1/market/providers/health`

- `GET /api/v1/market/btc/candles`
- `GET /api/v1/market/btc/candles/{timeframe}/latest`
- `GET /api/v1/market/btc/candles/latest`

- `GET /api/v1/market/btc/candles/{candle_id}`
- `GET /api/v1/market/btc/candles/{candle_id}/evidence`

- `GET /api/v1/intelligence/timeline`
- `GET /api/v1/intelligence/timeline/latest`
- `GET /api/v1/intelligence/timeline/window`
- `GET /api/v1/intelligence/timeline/context/{timeline_event_id}`

- `GET /api/v1/market/health`
- `GET /api/v1/market/btc/price/history`

- `/api/v1/news/{article_id}/score`

- `/api/v1/news/events/{event_id}/score`

- `/api/v1/news/high-impact`

- `/api/v1/news/security`

- `/api/v1/news/regulatory`

- `GET /api/v1/news/{article_id}/score`
- `GET /api/v1/news/events/{event_id}/score`
- `GET /api/v1/news/high-impact`
- `GET /api/v1/news/security`
- `GET /api/v1/news/regulatory`
- `GET /api/v1/news/by-sentiment/{label}`

- `GET /api/v1/news/{article_id}/scores`
- `GET /api/v1/news/{article_id}/narratives`
- `GET /api/v1/news/high-relevance`
- `GET /api/v1/intelligence/timeline/narratives/current`

- `GET /api/v1/news/{article_id}/impact`

- `GET /api/v1/news/{article_id}/explanation`

- `GET /api/v1/news/{article_id}/impact`
- `GET /api/v1/news/events/{event_id}/impact`
- `GET /api/v1/intelligence/timeline/news-impacts/high-confidence`
- `GET /api/v1/intelligence/timeline/news-impacts/recent`

### Candle Attribution API

- `GET /api/v1/intelligence/candles/{candle_id}/attribution` — calculate and return candidate news/event attributions for a BTC candle.
- `GET /api/v1/intelligence/candles/{candle_id}/top-events` — return persisted top-ranked candidate events for a BTC candle.
- `GET /api/v1/intelligence/candles/{candle_id}/replay` — return replay/debug snapshots for candle attribution runs.
- `GET /api/v1/intelligence/impact/high-confidence` — return high-confidence correlation-based news impact records.

### Production Candle Attribution Engine

- `GET /api/v1/intelligence/candles/{candle_id}/attribution` recalculates or returns ranked candle attribution candidates with confidence, limitations, and evidence references.
- `GET /api/v1/intelligence/candles/{candle_id}/explain` returns a frontend-ready candle explanation payload for chart markers, candle modal, side panel, and evidence drawer.
- `GET /api/v1/intelligence/candles/{candle_id}/candidates` returns persisted pre-ranking candidate rows and ranking features.
- `GET /api/v1/intelligence/candles/{candle_id}/replay` returns replay/debug snapshots for attribution runs.
- `PATCH /api/v1/intelligence/candles/attributions/{attribution_id}/review` records operator approval, rejection, false-attribution marking, confidence downgrade, or notes.

All candle attribution responses preserve the limitation that correlation is not proof of causation.
