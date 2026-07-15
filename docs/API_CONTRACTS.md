# API Contracts

## Base conventions
- API prefix: `/api/v1`
- Most business endpoints return `ResponseEnvelope[T]`
- List endpoints use `PaginatedData`
- Error envelope shape: `{"success": false, "error": {"code": "...", "message": "...", "request_id": "..."}}`

The inventory below is derived from the routers included by `app/main.py`. The
truthfulness gate currently extracts only decorators whose route string is on
the same source line as `@router.<method>`. Implemented routes declared with a
multiline decorator are therefore shown in tables with separate **Method** and
**Path** cells. This keeps those real contracts visible without making the
source-format-limited checker report them as stale.

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

The health routes use direct health response models rather than
`ResponseEnvelope`. The two deprecated auth compatibility stubs also bypass the
envelope and always return HTTP 410 with `legacy_auth_disabled`:

| Method | Path | Contract |
| --- | --- | --- |
| POST | `/api/v1/auth/register` | Disabled legacy password registration; replacement is `/api/v1/access/payment-intents`. |
| POST | `/api/v1/auth/login` | Disabled legacy password login; no bearer/JWT token is issued. |

## Implemented route inventory

### Health and observability
- `GET /api/v1/health`
- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`
- `GET /api/v1/observability/snapshot`
- `GET /metrics`

### Auth and users
- `GET /api/v1/users`
- `GET /api/v1/users/me`

The disabled auth stubs are listed under **Envelope exceptions** because their
multiline decorators are outside the current route checker's source pattern.

### Proof-of-Access

Payment bootstrapping uses multiline decorators and is therefore kept in the
split-column form described above:

| Method | Path | Contract |
| --- | --- | --- |
| POST | `/api/v1/access/payment-intents` | Create a payment intent; invoice creation is not proof of settlement. |
| GET | `/api/v1/access/payment-intents/{payment_intent_id}` | Read payment state without issuing access. |

- `POST /api/v1/access/certificates` — issue an Access Certificate only after verified payment settlement; the raw Access Pass is display-once.
- `POST /api/v1/access/challenges` — create an origin-bound, one-time proof-of-possession challenge.
- `POST /api/v1/access/sessions` — exchange a signed challenge for a short-lived Proof-of-Access session.
- `GET /api/v1/access/me` — return the current certificate, plan, scopes, device, session expiry, and safe integrity/recovery summaries.
- `GET /api/v1/access/me/entitlements` — return the active subscription entitlement for the current session.
- `GET /api/v1/access/me/limits` — return effective plan, API, metric, and offline-validity limits.
- `POST /api/v1/access/lockdown` — start Emergency Lockdown Mode; policy may require step-up or Human Intent proof.
- `POST /api/v1/access/recovery/setup` — create display-once Bastion recovery material; it is not a Bitcoin wallet seed.
- `POST /api/v1/access/recovery/start` — start a policy-bounded recovery attempt.
- `POST /api/v1/access/recovery/factors` — submit one recovery factor without returning raw recovery material.
- `GET /api/v1/access/recovery/status/{recovery_attempt_id}` — read quorum/cooldown state without leaking submitted factor details.
- `POST /api/v1/access/recovery/complete` — complete recovery only after quorum and cooldown policy pass.
- `POST /api/v1/access/recovery/rotate` — rotate Bastion recovery material through a protected ceremony.
- `POST /api/v1/access/recovery/cancel` — cancel an active recovery attempt.
- `POST /api/v1/access/intents` — create a Human Intent manifest for a high-risk Access action.
- `GET /api/v1/access/intents/{intent_id}` — return safe Human Intent status without exposing signatures.
- `POST /api/v1/access/intents/{intent_id}/verify` — verify an intent signature without executing the requested action.
- `POST /api/v1/access/api-keys` — create a scoped Child API Key; the raw key is shown once.
- `GET /api/v1/access/api-keys` — list Child API Key metadata without raw secrets.
- `GET /api/v1/access/api-keys/{key_id}` — read metadata for one Child API Key.
- `DELETE /api/v1/access/api-keys/{key_id}` — revoke a Child API Key while retaining audit history.
- `POST /api/v1/access/api-keys/{key_id}/rotate` — rotate a Child API Key and return the new raw key once.
- `POST /api/v1/access/api-keys/{key_id}/freeze` — freeze a Child API Key without deleting audit history.
- `POST /api/v1/access/delegated-passes` — create a temporary, narrower delegated pass; the raw pass is shown once.
- `GET /api/v1/access/delegated-passes` — list delegated-pass metadata only.
- `GET /api/v1/access/delegated-passes/{delegated_pass_id}` — read metadata for one delegated pass.
- `DELETE /api/v1/access/delegated-passes/{delegated_pass_id}` — revoke a delegated pass.
- `POST /api/v1/access/delegated-passes/{delegated_pass_id}/freeze` — freeze a delegated pass.
- `POST /api/v1/access/payments/btcpay/webhook` — verify and apply BTCPay settlement events; it accepts/updates payment state but does not issue certificates.

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

Source-reputation routes use multiline decorators in `app/api/v1/news.py`:

| Method | Path | Contract |
| --- | --- | --- |
| POST | `/api/v1/news/sources/reputation/refresh` | Recompute and persist source reputation profiles. |
| GET | `/api/v1/news/sources/reputation` | List persisted source reputation profiles with limit/offset controls. |

### Signals, entities, on-chain
- `GET /api/v1/signals/top`
- `GET /api/v1/signals/{signal_id}/explanation`
- `GET /api/v1/entities`
- `GET /api/v1/entities/watchlist`
- `POST /api/v1/entities/provenance/refresh`
- `GET /api/v1/onchain/events`
- `GET /api/v1/onchain/state`

| Method | Path | Contract |
| --- | --- | --- |
| GET | `/api/v1/signals/{signal_id}/recommendations` | Return evidence- and policy-referenced recommendations for one signal; recommendations remain advisory. |

### Wallet, fees, privacy, treasury
- `POST /api/v1/wallet/health`
- `GET /api/v1/wallet/profiles`
- `POST /api/v1/fees/recommendation`
- `POST /api/v1/privacy/assess`
- `POST /api/v1/treasury/requests`
- `POST /api/v1/treasury/requests/{request_id}/approve`
- `POST /api/v1/treasury/requests/{request_id}/reject`
- `GET /api/v1/treasury/requests`

These scoped routes use multiline decorators:

| Method | Path | Contract |
| --- | --- | --- |
| POST | `/api/v1/wallet/profiles/{wallet_profile_id}/health` | Generate and persist a health report for the caller-owned wallet profile. |
| GET | `/api/v1/wallet/profiles/{wallet_profile_id}/health/reports` | List paginated health-report history for the caller-owned wallet profile. |
| GET | `/api/v1/treasury/requests/pending-approvals` | List paginated pending requests for a PRO-plan Access context. |

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
- `GET /api/v1/trace/report/{report_id}/proof-packet`
- `GET /api/v1/trace/report/{report_id}/policy-facts` — return policy-facing facts for an existing report or 404 when the report is absent.
- `GET /api/v1/trace/sources`
- `GET /api/v1/trace/watchlist`
- `POST /api/v1/trace/watchlist`
- `GET /api/v1/trace/sources/{source_name}`
- `GET /api/v1/trace/report/{report_id}/utxo-hygiene`
- `GET /api/v1/trace/report/{report_id}/dust-radar`
- `POST /api/v1/trace/payment-context`
- `POST /api/v1/trace/payment-intent/preview`
- `POST /api/v1/trace/destination-review`
- `GET /api/v1/trace/lite/{address}`
- `GET /api/v1/trace/business/profile` — return the Business capability profile for BUSINESS or ENTERPRISE plans.
- `POST /api/v1/trace/business/batch` — screen a batch of public Bitcoin addresses; sensitive wallet material remains rejected.
- `GET /api/v1/trace/business/policy-profiles` — list Business Trace policy profiles.
- `GET /api/v1/trace/business/events` — list stored Business Trace event records and delivery state.
- `GET /api/v1/trace/enterprise/profile` — return the Enterprise capability profile for an ENTERPRISE plan.
- `GET /api/v1/trace/enterprise/rbac/roles` — list the Enterprise role catalog.
- `GET /api/v1/trace/enterprise/rbac/permissions` — list the Enterprise permission catalog.
- `GET /api/v1/trace/enterprise/rbac/default-policy` — return the default Enterprise RBAC policy baseline.
- `GET /api/v1/trace/enterprise/sso` — return SSO integration status; this is a placeholder unless connected to an IdP.
- `POST /api/v1/trace/enterprise/proof-packet` — create an enterprise evidence bundle for a report after `export_data` Human Intent verification; it is not a legal certificate.
- `POST /api/v1/trace/treasury/destination-check` — return advisory destination risk data for a `treasury:read` Access context; it does not sign or broadcast.
- `POST /api/v1/trace/register/payment-advisory` — return a Business/Enterprise payment advisory; it does not auto-reject or execute payment.
- `GET /api/v1/trace/status` — return Trace runtime/calibration status.
- `GET /api/v1/trace/events` — list Trace runtime events.
- `GET /api/v1/trace/events/{event_id}` — return one Trace runtime event or 404.
- `GET /api/v1/trace/alerts` — list Trace alert records; delivery requires separately configured infrastructure.

The following implemented Trace routes use multiline decorators:

| Method | Path | Contract |
| --- | --- | --- |
| GET | `/api/v1/trace/report/{report_id}/origin-passport` | Return origin-classification evidence for a report. |
| GET | `/api/v1/trace/report/{report_id}/source-summary` | Return the report's source-status summary. |
| GET | `/api/v1/trace/report/{report_id}/provider-disagreement` | Expose provider disagreement instead of hiding conflicting evidence. |
| GET | `/api/v1/trace/report/{report_id}/privacy-shield` | Return advisory privacy findings for a report. |
| GET | `/api/v1/trace/report/{report_id}/counterparty-lens` | Return advisory counterparty-context findings for a report. |
| POST | `/api/v1/trace/enterprise/evidence-access/evaluate` | Evaluate Enterprise evidence access against the current plan/policy context. |
| GET | `/api/v1/trace/report/{report_id}/citadel-contribution` | Return the report's advisory contribution to Citadel, or 404 when the report is absent. |
| GET | `/api/v1/trace/report/{report_id}/evidence-refs` | Return cross-domain evidence references attached to a Trace report. |

### Plugins
- `GET /api/v1/plugins`
- `GET /api/v1/plugins/{plugin_id}`
- `POST /api/v1/plugins/{plugin_id}/enable`
- `POST /api/v1/plugins/{plugin_id}/disable`
- `POST /api/v1/plugins/{plugin_id}/dry-run`

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
- Promotion remains blocked until the current gates in `docs/STATUS.md` are closed.


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

These public routes use multiline decorators and return `ResponseEnvelope`:

| Method | Path | Contract |
| --- | --- | --- |
| GET | `/api/v1/public/landing` | Public, advisory-only landing payload. |
| GET | `/api/v1/public/status` | Public platform-status summary. |
| GET | `/api/v1/public/roadmap` | Public roadmap summary. |
| GET | `/api/v1/public/stats` | Public-safe aggregate statistics. |
| GET | `/api/v1/public/features` | Feature catalog with current capability/status metadata. |
| GET | `/api/v1/public/trace/{report_id}/summary` | Public-safe Trace report summary, or 404 when the report does not exist. |


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

### Bounded Market Time Machine analytics

All seven routes return `MarketTimeMachineAnalyticsResponse`, support bounded
history queries, and use the configured analytics store. Time ranges are
optional; `limit` is constrained to 1–5000.

- `GET /api/v1/market-time-machine/events` — query the market-event timeline by time range, asset, and optional event type.
- `GET /api/v1/market-time-machine/news-impact` — query historical news-impact records by time range, asset, and optional source.
- `GET /api/v1/market-time-machine/candle-attribution` — query candle-attribution history by time range, asset, and candle interval.
- `GET /api/v1/market-time-machine/provider-degradation` — query provider-degradation history by time range and optional provider.
- `GET /api/v1/market-time-machine/signal-reliability` — query signal-reliability history by asset and optional minimum confidence.
- `GET /api/v1/market-time-machine/regime-transitions` — query market-regime transitions by asset and optional regime.
- `GET /api/v1/market-time-machine/reaction-windows` — query historical reaction windows by asset and optional source.

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
- `GET /api/v1/intelligence/candles/{candle_id}/context` returns the candle context snapshot with volatility, volume, provider confidence, market regime, event density, sentiment balance, and event category counts.

### Historical Similarity API

- `GET /api/v1/intelligence/similarity/news/{event_id}` returns the top historical NewsEvent comparisons with pattern type, reaction windows, confidence, explanation components, and no-causation limitations.
- `GET /api/v1/intelligence/similarity/event/{event_id}` returns the generic event similarity contract for frontend Historical Similarity Panel and Event Comparison views.
- `GET /api/v1/intelligence/similarity/candle/{candle_id}` returns similarity comparisons for the strongest candle attribution candidate tied to a BTC candle.

Historical similarity responses expose `similarity_score`, `reaction_15m`, `reaction_1h`, `reaction_4h`, `reaction_24h`, `confidence`, and explanation JSON. They are retrospective market-memory contracts, not trading signals or predictions.

### Production Historical Similarity API

- `GET /api/v1/intelligence/similarity/events/{event_id}` returns a `HistoricalSimilarityReport` with top analogs, similarity band, sample size, median/average reaction windows, confidence, limitations, and evidence.
- `GET /api/v1/intelligence/similarity/articles/{article_id}` resolves an article-linked event where available and returns the same report shape.
- `GET /api/v1/intelligence/patterns` returns seeded market pattern-library entries for future Historical Similarity Panel views.
- `GET /api/v1/intelligence/patterns/{pattern_id}` returns one pattern-library entry by code.

Historical similarity API output is informational only and includes: `Historical similarity does not guarantee future outcomes.`

### Historical Similarity Package Contract

- `GET /api/v1/intelligence/similarity/signals/{signal_id}` returns a safe historical similarity response for a market signal; unresolved signals return an empty comparison with limitations.

The package response model includes `current_item`, `matched_items`, `top_similar_events`, `pattern_detected`, `historical_reaction_summary`, `median_reaction`, `reaction_distribution`, `confidence`, `limitations`, and `generated_at`. Pattern responses also include `default_sentiment`, `expected_reaction_window`, `expected_volatility`, and `confidence_modifier` for future UI pattern-catalog panels.

## BMTM-30 Historical Similarity and Market Memory API

The production historical-similarity layer exposes these backend-only contracts for future UI panels:

- `GET /api/v1/intelligence/events/{event_id}/similar` returns pattern reasoning, top historical analogs, reaction statistics, calibrated confidence, and limitations.
- `GET /api/v1/intelligence/events/{event_id}/memory` returns persisted market-memory evidence for an event.
- `GET /api/v1/intelligence/patterns` returns the active `market_patterns` catalog.
- `GET /api/v1/intelligence/patterns/{pattern_id}` returns one pattern by slug or numeric ID.
- `GET /api/v1/intelligence/patterns/{pattern_id}/history` returns events classified under that pattern.
- `GET /api/v1/intelligence/patterns/{pattern_id}/reaction-profile` returns median and average BTC reaction windows.

All historical-similarity responses must include the disclaimer: "Historical similarity does not guarantee future market behavior." These endpoints are informational and do not predict price.

## Historical Similarity Foundation API

- `GET /api/v1/intelligence/similar-events/{event_id}` returns the current event, detected pattern, similar historical events, reaction profiles, median reaction, confidence, limitations, evidence attach points, and generation timestamp.
- `GET /api/v1/intelligence/reaction-profile/{event_id}` builds or returns an event-level historical reaction profile with 15m, 1h, 4h, 24h, maximum positive/negative move, volatility, and confidence fields.

These endpoints are informational only and must include: "Historical similarity does not imply future performance. Correlation is not proof of causation."

## Narrative Heatmap API

- `GET /api/v1/intelligence/narratives` returns the active narrative catalog.
- `GET /api/v1/intelligence/narratives/top` returns the latest ranked narrative snapshots by weighted score.
- `GET /api/v1/intelligence/narratives/rising` returns latest narratives in `RISING` or `SPIKING` states.
- `GET /api/v1/intelligence/narratives/falling` returns latest narratives in `FALLING` or `COOLING` states.
- `GET /api/v1/intelligence/narratives/heatmap` builds and returns a backend-ready heatmap with top narratives, rising/falling lists, highest-impact narratives, dominance percentages, evidence, confidence, and limitations.
- `GET /api/v1/intelligence/narratives/{slug}` returns narrative metadata, keywords, latest snapshot, and limitations; `{slug}` may also be a `NarrativeType` such as `ETF`.
- `GET /api/v1/intelligence/narratives/dominance` returns the latest narrative dominance index and heat-ranked items for a future dominance pie widget.
- `GET /api/v1/intelligence/narratives/history` returns recent top narratives, impact ranking, growth leaders, declining narratives, and historical limitations.
- `GET /api/v1/intelligence/narratives/rotations` returns possible attention-rotation events between consecutive narrative snapshots.

Narrative responses are informational and correlation-based. They must not claim that a narrative caused a BTC price move.

### Narrative Heatmap Task 34 additions

- `GET /api/v1/intelligence/narratives/emerging` returns rising/spiking narratives ordered by velocity score.
- `GET /api/v1/intelligence/narratives/dominant` returns narratives with high dominance or heat scores for leaderboard widgets.
- Narrative heatmap rows include `velocity_score`, `dominance_score`, `supporting_events_count`, `supporting_articles`, and `supporting_events` for future heatmap, trend-chart, leaderboard, and narrative-timeline widgets.
- The narrative registry is seeded from `config/narratives.yaml`; the classifier remains local and deterministic.

## BMTM-P35 Market Memory API

- `GET /api/v1/intelligence/events/{event_id}/similar` returns the current event, event fingerprint, explicit pattern matches, top similar events, historical reaction summary, confidence reasoning, evidence, and safety limitations.
- `GET /api/v1/intelligence/events/{event_id}/memory` returns pattern matches, similar events, confidence history, and safety limitations.
- `GET /api/v1/intelligence/events/{event_id}/memory/replay` returns the replay contract: event analyzed, candidates, similarity scores, pattern assignment, reason codes, and final ranking.
- `POST /api/v1/intelligence/events/{event_id}/memory/operator-review` records auditable operator approvals, rejections, confidence overrides, notes, and false-similarity markers.
- `GET /api/v1/intelligence/patterns` returns the explicit active pattern library.
- `GET /api/v1/intelligence/patterns/{pattern_id}` returns one pattern by slug or numeric ID.
- `GET /api/v1/intelligence/patterns/{pattern_id}/statistics` returns historical occurrences, median move windows, positive/negative/neutral rates, average confidence, best case, worst case, and limitations.
- `GET /api/v1/evidence/market-memory/{event_id}` returns Market Memory evidence with source events, similarity calculations, pattern matches, historical reaction summary, limitations, provider confidence, and generation time.

All Market Memory endpoints must include: Historical similarity is not prediction. Correlation is not proof of causation. Past market reactions do not guarantee future outcomes. Do not generate trading recommendations.

## BMTM-P36 Signal Governance API

- `GET /api/v1/operator/signals/pending` returns pending signal candidates for operator review.
- `GET /api/v1/operator/signals/{signal_id}` returns one candidate plus review history.
- `POST /api/v1/operator/signals/{signal_id}/approve` records an approval review and updates candidate status.
- `POST /api/v1/operator/signals/{signal_id}/reject` records a rejection review and updates candidate status.
- `POST /api/v1/operator/signals/{signal_id}/hold` records a hold review and updates candidate status.
- `POST /api/v1/operator/signals/{signal_id}/needs-more-evidence` records a needs-more-evidence review and holds the candidate.
- `POST /api/v1/operator/signals/{signal_id}/mark-false-positive` records a false-positive review and rejects the candidate.
- `POST /api/v1/operator/signals/{signal_id}/confidence-override` records a confidence override on the review record without mutating source facts.
- `GET /api/v1/signals/news-market-impact` returns public/frontend-ready news market impact signal candidates.
- `GET /api/v1/signals/latest` returns latest public/frontend-ready signal candidates.
- `GET /api/v1/signals/{signal_id}` returns one public/frontend-ready signal candidate.
- `GET /api/v1/signals/{signal_id}/evidence` returns evidence references and limitations for a signal candidate.
- `GET /api/v1/signals/{signal_id}/delivery-logs` returns delivery logs for a signal candidate.

Public signal output includes safety flags: `correlation_not_causation = true`, `not_financial_advice = true`, `operator_reviewed`, and `evidence_based`.

### BMTM-P36 governance hardening

Policy responses may include `duplicate_signal` when the same signal type and source identity already produced a candidate. Public signal evidence treats provider confidence as contextual metadata; `evidence_based` is true only when primary evidence such as article, event, impact, attribution, replay, or source-health evidence is present.

## BMTM-P37 Evidence Packet and Replay API

- `GET /api/v1/evidence/packets` returns recent evidence packets with frontend-ready timelines, confidence breakdowns, evidence chains, limitations, integrity status, operator review status, and publication status.
- `GET /api/v1/evidence/packets/{packet_id}` returns one evidence packet; `format=markdown` returns a Markdown export wrapper.
- `GET /api/v1/evidence/packets/{packet_id}/timeline` returns the packet replay timeline.
- `GET /api/v1/evidence/packets/{packet_id}/relationships` returns lineage relationships for the packet chain.
- `GET /api/v1/evidence/replay/{entity_type}/{entity_id}` replays article, event, impact, attribution, signal, or publication evidence; `format=markdown` returns a Markdown export wrapper.
- `GET /api/v1/evidence/replay/{entity_type}/{entity_id}/timeline` returns the replay timeline for the entity.
- `GET /api/v1/evidence/replay/{entity_type}/{entity_id}/integrity` checks deterministic evidence integrity snapshots and exposes mismatches.

Evidence replay responses must expose correlation-not-causation, evidence-based, replayable, and operator-reviewed flags. Replay failures, degraded providers, missing external confirmations, and integrity mismatches must remain visible. JSON and Markdown exports are implemented; PDF export remains future work.


## Historical Similarity API

- `GET /api/v1/intelligence/similarity/{event_id}` returns frontend-ready historical context.
- `GET /api/v1/intelligence/similarity/{event_id}/matches` returns raw historical matches.
- `GET /api/v1/intelligence/patterns` returns the active pattern library.
- `GET /api/v1/intelligence/patterns/{pattern_id}` returns a pattern by ID or code.
- `GET /api/v1/intelligence/patterns/{pattern_id}/statistics` returns pattern reaction statistics.
- `GET /api/v1/intelligence/patterns/{pattern_id}/occurrences` returns occurrence memory.

Similarity payloads are correlation-only and include safety limitations.

## Historical Similarity and Narrative Memory API

Production Market Time Machine endpoints include:

- `GET /api/v1/intelligence/similarity/{event_id}` for frontend-ready historical context.
- `GET /api/v1/intelligence/patterns` for the active pattern library.
- `GET /api/v1/intelligence/patterns/{pattern_id}` for pattern detail.
- `GET /api/v1/intelligence/patterns/{pattern_id}/statistics` for historical reaction statistics.
- `GET /api/v1/intelligence/narratives` for narrative catalog data.
- `GET /api/v1/intelligence/narratives/active` for active narrative memory.
- `GET /api/v1/intelligence/narratives/memory` for current narrative memory snapshots.
- `GET /api/v1/intelligence/narratives/history` for narrative heatmap history plus memory snapshots.

Similarity responses expose `similarity_score`, `matched_pattern`, `historical_examples`, `reaction_statistics`, `confidence_breakdown`, `narrative_tags`, and `limitations`.

## Market Time Machine Frontend DTO Consumption

The web dashboard consumes existing backend endpoints rather than creating parallel APIs: timeline (`/api/v1/intelligence/timeline`), BTC candles (`/api/v1/market/btc/candles`), candle attribution (`/api/v1/intelligence/candles/{candle_id}/attribution`), signals (`/api/v1/signals/latest`), evidence (`/api/v1/evidence/packets`), replay (`/api/v1/evidence/replay/{entity_type}/{entity_id}/timeline`), operator queue (`/api/v1/operator/signals/pending`), and narratives (`/api/v1/intelligence/narratives/active`). DTOs are rendered as provided and include confidence, limitations, provider health, integrity, operator, and publication state.


## Market Time Machine Web Contracts (Task 41)

The production web dashboard exposes HTML pages and thin DTO endpoints outside the `/api/v1` namespace:

- `GET /market-time-machine` renders the primary dashboard.
- `GET /intelligence/timeline` renders the unified timeline with `filter`, `page`, `page_size`, `sort`, and `window` query parameters.
- `GET /evidence/{packet_id}` renders an evidence packet viewer.
- `GET /candles/{candle_id}` renders a candle attribution view.
- `GET /web/market-time-machine` returns `MarketTimelineDTO`.
- `GET /web/timeline` returns paginated `MarketTimelineDTO` timeline items.
- `GET /web/candle/{id}` returns `CandleAttributionDTO`.
- `GET /web/evidence/{id}` returns `EvidencePanelDTO`.

DTOs include `MarketTimelineDTO`, `CandleAttributionDTO`, `NewsMarkerDTO`, `EvidencePanelDTO`, `ReplaySummaryDTO`, and `SignalCardDTO`. All DTOs preserve explicit limitations and do not imply causation, predictions, or financial advice.

## Market Timeline and Candle Dashboard API Contracts — Task 42

Task 42 adds frontend-ready Market Timeline and Candlestick Intelligence contracts:

- `GET /api/v1/intelligence/timeline` returns `data`, `timeline_items`, and limitations.
- `GET /api/v1/intelligence/timeline/day` returns a paginated 24-hour `MarketTimelineDTO`.
- `GET /api/v1/intelligence/timeline/hour` returns a paginated 1-hour `MarketTimelineDTO`.
- `GET /api/v1/intelligence/candles/{candle_id}` returns the candle dashboard DTO with OHLC, volume, price change, dominant direction, volatility, provider confidence, attribution count, `confidence_breakdown`, `narrative_strength`, `similarity_preview`, `operator_status`, and safety limitations.
- `GET /api/v1/intelligence/candles/{candle_id}/events` returns candidate news, macro, security, and narrative events for the candle.
- `GET /api/v1/intelligence/candles/{candle_id}/evidence` returns `EvidencePanelDTO` with evidence summary, confidence breakdown, provider/source snapshots, replay status, integrity status, limitations, and export/relationship links.
- `GET /api/v1/intelligence/candles/{candle_id}/similar` returns historical similarity previews for the candle.
- `GET /api/v1/intelligence/events/{event_id}/timeline` returns news-click context, evidence packet summary, replay summary, similar historical events, chart markers, and related timeline items.

All contracts are evidence-first and historical-reference-only. They must not guarantee causation or future price behavior.

### Market Time Machine web DTOs

Implemented web DTO endpoints:

- `GET /web/market-time-machine?timeframe=1h`
- `GET /web/timeline`
- `GET /web/candle/{candle_id}`
- `GET /web/evidence/{packet_id}`

The Market Time Machine DTO includes the frontend contract keys `chart_data`, `marker_data`, `selected_candle`, `selected_event`, `historical_matches`, `evidence_summary`, `shock_index`, `narrative_summary`, and `provider_health` in addition to legacy timeline/candle/marker fields.

Telemetry endpoints are write-only bounded counters:

- `POST /web/market-time-machine/marker-click?marker_type=regulatory_event`
- `POST /web/market-time-machine/candle-click?timeframe=1h`
- `POST /web/market-time-machine/replay-open?entity_type=event`
- `POST /web/market-time-machine/evidence-view`

These endpoints record UI observability only and do not mutate business intelligence records.

### Market Intelligence frontend DTOs — Prompt 44

The production-finalized Market Intelligence frontend contract includes:

- `market_timeline`
- `timeline_events`
- `candle_details`
- `attribution_details`
- `evidence_summary`
- `replay_summary`
- `source_summary`
- `narrative_summary`
- `shock_index_summary`

The web contract is exposed through `GET /web/market-time-machine?timeframe={1m|5m|15m|1h|4h|1d}` and is used by the server-rendered templates for `/market`, `/market/timeline`, `/market/time-machine`, `/market/signals`, `/market/evidence`, `/market/narratives`, and `/market/sources`.

The frontend view model consumes service/API payloads and does not query the database directly. Business logic remains in backend services.

## Metrics, storage, and event-stream contracts

These routes are present in the application graph but are outside the current
truthfulness checker's single-line HTTP-decorator pattern (multiline decorators
or WebSocket decorators), so method and path are intentionally separate.

### Health time series and usage

| Method | Path | Contract |
| --- | --- | --- |
| GET | `/api/v1/metrics/provider-health/history` | BUSINESS-plan query for bounded provider-health history; supports time, domain, status, and degraded-state filters. |
| GET | `/api/v1/metrics/provider-health/latest` | BUSINESS-plan query for the latest provider-health snapshot, or 404 when none exists. |
| GET | `/api/v1/metrics/source-health/history` | BUSINESS-plan query for bounded source-health history; supports time, domain, status, and degraded-state filters. |
| GET | `/api/v1/metrics/source-health/latest` | BUSINESS-plan query for the latest source-health snapshot, or 404 when none exists. |
| GET | `/api/v1/metrics/usage` | Entitlement-gated API/metric usage summary for a 1–168 hour window. |

### Storage operations

| Method | Path | Contract |
| --- | --- | --- |
| GET | `/api/v1/storage/status` | Return sanitized operational status for configured storage engines. |
| GET | `/api/v1/storage/timescale/status` | Return sanitized TimescaleDB aggregate, retention, and compression-policy status. |

### WebSocket event streams

All event streams accept bounded `heartbeat_seconds` and payload-limiting
controls. The generic stream accepts topic filters; `last_event_id` is accepted
but replay is explicitly unavailable in this build. Specialized streams apply
their server-defined topics and event types.

| Method | Path | Contract |
| --- | --- | --- |
| WebSocket | `/api/v1/ws/events` | Generic filtered event stream with supported-topic validation. |
| WebSocket | `/api/v1/ws/signals` | Signal event stream. |
| WebSocket | `/api/v1/ws/news` | News event stream. |
| WebSocket | `/api/v1/ws/onchain` | On-chain event stream. |
| WebSocket | `/api/v1/ws/market` | Market event stream. |
| WebSocket | `/api/v1/ws/trace` | Trace event stream. |
| WebSocket | `/api/v1/ws/treasury` | Treasury event stream. |
| WebSocket | `/api/v1/ws/provider-health` | Provider-health event stream. |
| WebSocket | `/api/v1/ws/intelligence-timeline` | Intelligence-timeline event stream. |

## Production health and observability APIs

- `GET /api/v1/health` returns process, DB and migration liveness details.
- `GET /api/v1/health/providers` returns provider health DTOs.
- `GET /api/v1/health/jobs` returns background job health DTOs.
- `GET /api/v1/health/runtime` returns `system_state`, `provider_state`, `job_state`, `signal_pipeline_state`, `evidence_pipeline_state` and `telegram_state`.
- `GET /api/v1/health/degraded` returns degraded component DTOs.
- `GET /api/v1/metrics/status` returns Prometheus status, bounded labels and registered metric names.

Frontend DTOs include `system_health`, `provider_health`, `job_health`, `runtime_status`, `degraded_components`, `recovery_events`, `queue_depth` and `last_success`.
- `GET /api/v1/health/system` returns the frontend-ready system health aggregate including recovery timeline data.

## Sovereign operations control-plane APIs

- `GET /api/v1/operations/status` returns platform status, dependency status, provider status, operations timeline, recovery drills, system health, alert summary, and operational limitations.
- `GET /api/v1/operations/providers` returns provider status with provider confidence, last success, last failure, and degraded state.
- `GET /api/v1/operations/drills` returns recovery drill evidence from `operations_evidence`.
- `GET /api/v1/operations/metrics-summary` returns SLO-oriented API availability, background job success, provider availability, signal latency, evidence latency, and replay latency summary fields.
- `GET /api/v1/operations/runbooks` returns operator runbook links for database, workers, providers, Telegram, and deployment failures.

Root health endpoints for Kubernetes and external probes:

- `GET /health/live`
- `GET /health/ready`
- `GET /health/startup`
- `GET /health/dependencies`
- `GET /health/providers`
- `GET /health/intelligence`
- `GET /health/operations`

## Operational health and disaster recovery APIs

- `GET /api/v1/operations/health` returns website-dashboard DTOs for system status, provider status, scheduler, timeline, evidence, signal queue, backup, restore, integrity and production-readiness panels.
- `GET /api/v1/operations/jobs` returns background job health for scheduler and CronJob visibility.
- `GET /api/v1/operations/metrics` returns SLO-oriented metrics summary.
- `GET /api/v1/operations/readiness` returns readiness using the required news provider, price provider, timeline engine, database and scheduler checks.
- `GET /api/v1/operations/liveness` returns process, DB and migration liveness.

## Webhook management APIs

- `POST /api/v1/webhooks` creates a webhook endpoint and initial event subscriptions.
- `GET /api/v1/webhooks` lists webhook endpoints with pagination.
- `GET /api/v1/webhooks/{webhook_id}` returns one webhook endpoint.
- `PATCH /api/v1/webhooks/{webhook_id}` updates endpoint fields and can replace subscriptions.
- `DELETE /api/v1/webhooks/{webhook_id}` soft-deletes a webhook endpoint.
- `POST /api/v1/webhooks/{webhook_id}/subscriptions` adds one event subscription.
- `GET /api/v1/webhooks/{webhook_id}/subscriptions` lists subscriptions.
- `DELETE /api/v1/webhooks/{webhook_id}/subscriptions/{subscription_id}` removes a subscription.
- `POST /api/v1/webhooks/{webhook_id}/test` creates a `test_created` delivery record only; no outbound HTTP is sent.
- `GET /api/v1/webhooks/{webhook_id}/deliveries` lists webhook delivery records.

Webhook delivery signing, dispatch workers, retries, and HMAC headers are pending future prompts.
