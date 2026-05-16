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


### Mining (planned, not implemented yet)
Status: **PLANNED** for all routes in this section (not currently implemented runtime endpoints).

- `GET /api/v1/mining/pools`
- `GET /api/v1/mining/pools/{pool_id}`
- `GET /api/v1/mining/stratum-v2/adoption`
- `GET /api/v1/mining/sovereignty-score`
- `GET /api/v1/mining/censorship-risk`
- `GET /api/v1/mining/template-control`
- `GET /api/v1/mining/signals`

#### Envelope contract (planned)
All planned mining routes follow `ResponseEnvelope[T]`:
- success: `{"success": true, "data": ...}`
- error: `{"success": false, "error": {"code", "message", "request_id"}}`

#### Planned response shape requirements (applies to every mining endpoint)
Each endpoint response payload must include:
- `freshness`
- `confidence_score`
- `source_quality` (`source_type`, `provider_name`, `is_verified`, `is_fallback`, `is_synthetic`)
- `limitations`
- `evidence_refs`
- `explainability` (drivers, factor breakdown, and source-quality impact)

#### Planned endpoint payload drafts
1. `GET /api/v1/mining/pools`
   - `data.items[]`: `{pool_id, pool_name, hashrate_share_pct, pool_sovereignty_score_100, confidence_score, source_quality, explainability}`
   - `data.total`, `data.limit`, `data.offset`

2. `GET /api/v1/mining/pools/{pool_id}`
   - `data`: `{pool_id, pool_name, capability_states, template_control_owner, pool_sovereignty_score_100, mining_censorship_risk_score_100, confidence_score, source_quality, explainability}`

3. `GET /api/v1/mining/stratum-v2/adoption`
   - `data`: `{network_adoption_state, pools[], coverage_ratio, confidence_score, source_quality, explainability}`

4. `GET /api/v1/mining/sovereignty-score`
   - `data`: `{pool_scope, pool_sovereignty_score_100, severity, factor_breakdown, confidence_score, source_quality, explainability}`

5. `GET /api/v1/mining/censorship-risk`
   - `data`: `{pool_scope, mining_censorship_risk_score_100, mining_censorship_risk_level, factor_breakdown, confidence_score, source_quality, explainability}`

6. `GET /api/v1/mining/template-control`
   - `data`: `{path_observation, template_control_state, template_control_owner, template_sovereignty_score_100, template_interference_risk_score_100, mitm_risk_level, confidence_score, source_quality, explainability}`

7. `GET /api/v1/mining/signals`
   - `data.items[]`: `{signal_id, signal_type, severity, confidence_score, source_quality, freshness, limitations, evidence_refs, explainability}`
   - `data.total`, `data.limit`, `data.offset`
